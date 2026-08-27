"""HTTP 客户端 — 通过 Chrome CDP 代理请求

同花顺使用 hexin-v 动态反爬标头（由 chameleon 库在浏览器 localStorage 中生成），
Python 直接请求会 401。所有 API 请求通过 CDP Runtime.evaluate 在浏览器内执行 fetch。
"""

from __future__ import annotations

import json
import random
import time
from typing import Any

from . import auth
from .auth import cdp_evaluate, get_cookies, clear as clear_cookies

API_PREFIX = "/caishen_httpserver/tzzb"

# 空模板特征：页面未加载完成时 API 返回的默认空数据
# upload_time 为空字符串是关键区分标识（真实空账户也不会有 upload_time）
EMPTY_TEMPLATE_INDICATORS = {"upload_time": ""}


class TzzbError(Exception):
    """投资账本 API 错误"""

    def __init__(self, message: str, error_code: str = "", status_code: int = 0):
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(message)


def _is_empty_template(ex_data: dict) -> bool:
    """检测是否为页面未加载完成时的空模板响应"""
    if not isinstance(ex_data, dict):
        return False
    # 空模板特征：upload_time 为空字符串
    if ex_data.get("upload_time") == "":
        return True
    return False


def _request_raw(endpoint: str, params: dict[str, Any] | None = None) -> dict:
    """单次 API 请求（不含重试逻辑）"""
    cookies = get_cookies()
    if not cookies:
        raise TzzbError("未登录，请先调用 tzzb_login 完成认证", status_code=401)

    userid = cookies.get("userid", "")
    _nonce = str(random.randint(100000, 999999))

    body_parts = {
        "terminal": "1",
        "version": "0.0.0",
        "userid": userid,
        "user_id": userid,
        "_nc": _nonce,  # 防缓存 nonce，确保每次请求 body 不同
        **(params or {}),
    }
    body_str = "&".join(f"{k}={v}" for k, v in body_parts.items())

    js_code = f"""
    (async () => {{
        try {{
            const resp = await fetch('{API_PREFIX}{endpoint}?_t=' + Date.now(), {{
                method: 'POST',
                headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                body: {json.dumps(body_str)},
                cache: 'no-store'
            }});
            const text = await resp.text();
            return JSON.stringify({{
                status: resp.status,
                body: text,
                ok: resp.ok
            }});
        }} catch(e) {{
            return JSON.stringify({{
                status: 0,
                body: e.message,
                ok: false
            }});
        }}
    }})()
    """

    try:
        cdp_result = cdp_evaluate(js_code)
        result = json.loads(cdp_result["result"]["result"]["value"])
    except KeyError as e:
        raise TzzbError(f"CDP 响应解析失败: {e}", status_code=500)
    except Exception as e:
        raise TzzbError(f"CDP 请求失败（已自动重连重试）: {e}", status_code=500)

    status = result.get("status", 0)
    body_text = result.get("body", "")

    if status == 401:
        clear_cookies()
        raise TzzbError("Cookie 已过期，请重新调用 tzzb_login", status_code=401)
    if status == 502:
        clear_cookies()
        raise TzzbError("服务端异常，请重新调用 tzzb_login", status_code=502)
    if status != 200:
        raise TzzbError(f"HTTP {status}: {body_text[:200]}", status_code=status)

    try:
        data = json.loads(body_text)
    except json.JSONDecodeError:
        raise TzzbError(f"响应解析失败: {body_text[:200]}")

    if data.get("error_code") != "0":
        raise TzzbError(
            data.get("error_msg", "请求异常"),
            error_code=str(data.get("error_code", "")),
        )

    return data.get("ex_data", {})


def request(
    endpoint: str,
    params: dict[str, Any] | None = None,
    max_retries: int = 3,
) -> dict:
    """同步 API 请求：通过 CDP 在浏览器内执行 fetch，带空模板检测和重试

    页面未加载完成时（hexin-v 标头未生成），API 会返回空模板（HTTP 200 + error_code 0），
    不会抛异常。需要通过 upload_time 判断并触发重试。
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            ex_data = _request_raw(endpoint, params)
        except TzzbError as e:
            # 网络/认证错误，直接重试
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(1)
            continue

        # 检查是否为页面未加载完成时的空模板
        if _is_empty_template(ex_data):
            last_error = TzzbError(
                "API 返回空模板（页面可能未加载完成），正在重试...",
                status_code=503,
            )
            if attempt < max_retries - 1:
                # 等待页面加载完成后再重试
                time.sleep(2)
            continue

        return ex_data

    if last_error:
        raise last_error
    return {}  # 不应到达