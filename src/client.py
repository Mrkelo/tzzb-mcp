"""HTTP 客户端封装"""

from typing import Any

import httpx

from .auth import get_cookies, clear as clear_cookies

BASE_URL = "https://tzzb.10jqka.com.cn"
API_PREFIX = "/caishen_httpserver/tzzb"


class TzzbError(Exception):
    """投资账本 API 错误"""

    def __init__(self, message: str, error_code: str = "", status_code: int = 0):
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(message)


async def _request(endpoint: str, params: dict[str, Any] | None = None, retries: int = 1) -> dict:
    """发送 API 请求

    Args:
        endpoint: API 路径，如 /caishen_fund/pc/account/v1/account_list
        params: 额外请求参数
        retries: 重试次数
    """
    cookies = get_cookies()
    if not cookies:
        raise TzzbError("未登录，请先调用 tzzb_login 完成认证", status_code=401)

    userid = cookies.get("userid", "")
    data = {
        "terminal": "1",
        "version": "0.0.0",
        "userid": userid,
        "user_id": userid,
        **(params or {}),
    }

    url = f"{BASE_URL}{API_PREFIX}{endpoint}"
    last_error: Exception | None = None

    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(
                cookies=cookies,
                timeout=httpx.Timeout(30.0),
                follow_redirects=True,
            ) as client:
                r = await client.post(
                    url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                # Cookie 过期
                if r.status_code == 401:
                    clear_cookies()
                    raise TzzbError("Cookie 已过期，请重新调用 tzzb_login", status_code=401)

                # 服务端异常
                if r.status_code == 502:
                    clear_cookies()
                    raise TzzbError("服务端异常，Cookie 可能已过期，请重新调用 tzzb_login", status_code=502)

                # 频率限制
                if r.status_code == 403:
                    if attempt < retries:
                        import asyncio
                        await asyncio.sleep(3)
                        continue
                    raise TzzbError("请求被频率限制，请稍后重试", status_code=403)

                if r.status_code != 200:
                    raise TzzbError(f"HTTP {r.status_code}: {r.text[:200]}", status_code=r.status_code)

                result = r.json()
                if result.get("error_code") != "0":
                    raise TzzbError(
                        result.get("error_msg", "请求异常"),
                        error_code=str(result.get("error_code", "")),
                    )

                return result.get("ex_data", {})

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            last_error = e
            if attempt < retries:
                import asyncio
                await asyncio.sleep(2)
                continue
            raise TzzbError(f"网络请求失败: {e}") from e

    raise TzzbError(f"请求失败: {last_error}")


async def request(endpoint: str, params: dict[str, Any] | None = None) -> dict:
    """公开 API 请求接口"""
    return await _request(endpoint, params)


async def request_raw(endpoint: str, params: dict[str, Any] | None = None) -> dict:
    """发送原始请求，返回完整响应（不解析 error_code）"""
    cookies = get_cookies()
    if not cookies:
        raise TzzbError("未登录，请先调用 tzzb_login 完成认证", status_code=401)

    userid = cookies.get("userid", "")
    data = {
        "terminal": "1",
        "version": "0.0.0",
        "userid": userid,
        "user_id": userid,
        **(params or {}),
    }

    url = f"{BASE_URL}{API_PREFIX}{endpoint}"
    async with httpx.AsyncClient(
        cookies=cookies,
        timeout=httpx.Timeout(30.0),
        follow_redirects=True,
    ) as client:
        r = await client.post(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return r.json()
