"""HTTP 客户端 — 通过 Chrome CDP 代理请求"""

from __future__ import annotations

import json
import time
from typing import Any

import httpx
import websocket

from .auth import get_cookies, clear as clear_cookies

CHROME_PORT = 9222
API_PREFIX = "/caishen_httpserver/tzzb"


class TzzbError(Exception):
    """投资账本 API 错误"""

    def __init__(self, message: str, error_code: str = "", status_code: int = 0):
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(message)


def _get_mcp_page() -> dict:
    """获取投资账本页面的 CDP target"""
    r = httpx.get(f"http://localhost:{CHROME_PORT}/json", timeout=5)
    targets = r.json()
    for t in targets:
        if t.get("type") == "page" and "tzzb" in t.get("url", ""):
            return t
    raise TzzbError("未找到投资账本页面，请确保 Chrome 已打开并登录 tzzb.10jqka.com.cn", status_code=401)


def _cdp_fetch(endpoint: str, params: dict[str, Any] | None = None) -> dict:
    """通过 CDP 在浏览器中执行 fetch 请求

    同花顺使用 hexin-v 动态反爬标头（由 chameleon 库生成），
    无法在 Python 中模拟，必须通过浏览器原生网络栈发起请求。
    """
    cookies = get_cookies()
    if not cookies:
        raise TzzbError("未登录，请先调用 tzzb_login 完成认证", status_code=401)

    userid = cookies.get("userid", "")

    # 构建 POST body
    body_parts = {
        "terminal": "1",
        "version": "0.0.0",
        "userid": userid,
        "user_id": userid,
        **(params or {}),
    }
    body_str = "&".join(f"{k}={v}" for k, v in body_parts.items())

    # 构建 JS fetch 代码
    js_code = f"""
    (async () => {{
        try {{
            const resp = await fetch('{API_PREFIX}{endpoint}', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                body: {json.dumps(body_str)}
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

    # 连接 CDP
    page = _get_mcp_page()
    ws = websocket.WebSocket()
    ws.settimeout(30)
    ws.connect(page["webSocketDebuggerUrl"])

    ws.send(
        json.dumps(
            {
                "id": 1,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": js_code,
                    "awaitPromise": True,
                    "returnByValue": True,
                },
            }
        )
    )
    response = json.loads(ws.recv())
    ws.close()

    result = json.loads(response["result"]["result"]["value"])
    status = result.get("status", 0)
    body_text = result.get("body", "")

    # 处理 HTTP 错误
    if status == 401:
        clear_cookies()
        raise TzzbError("Cookie 已过期，请重新调用 tzzb_login", status_code=401)
    if status == 502:
        clear_cookies()
        raise TzzbError("服务端异常，Cookie 可能已过期，请重新调用 tzzb_login", status_code=502)
    if status != 200:
        raise TzzbError(f"HTTP {status}: {body_text[:200]}", status_code=status)

    # 解析响应
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


def request(endpoint: str, params: dict[str, Any] | None = None) -> dict:
    """同步 API 请求（MCP 工具调用）"""
    return _cdp_fetch(endpoint, params)


async def request_async(endpoint: str, params: dict[str, Any] | None = None) -> dict:
    """异步 API 请求"""
    return _cdp_fetch(endpoint, params)