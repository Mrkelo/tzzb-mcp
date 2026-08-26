"""Cookie 提取与认证管理"""

import json
import os
import time
import subprocess
from pathlib import Path

import httpx
import websocket

from .models import LoginStatus

COOKIE_FILE = Path.home() / ".tzzb_cookies.json"
REQUIRED_COOKIES = {"userid", "ticket", "user"}
CHROME_PORT = 9222
CHROME_URL = "https://tzzb.10jqka.com.cn/pc/index.html#/unlogin"


def _load_cookies() -> dict[str, str] | None:
    """从本地文件加载 Cookie"""
    if not COOKIE_FILE.exists():
        return None
    try:
        data = json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
        if REQUIRED_COOKIES.issubset(data.keys()):
            return {k: data[k] for k in REQUIRED_COOKIES}
    except Exception:
        pass
    return None


def _save_cookies(cookies: dict[str, str]) -> None:
    """保存 Cookie 到本地文件"""
    data = {**cookies, "extracted_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "source": "chrome_cdp"}
    COOKIE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _clear_cookies() -> None:
    """清除本地 Cookie"""
    COOKIE_FILE.unlink(missing_ok=True)


def _find_chrome() -> str | None:
    """查找 Chrome 可执行文件路径"""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    return next((p for p in candidates if os.path.exists(p)), None)


def launch_chrome() -> dict:
    """启动带调试端口的 Chrome，返回状态信息"""
    # 已运行则直接返回
    try:
        r = httpx.get(f"http://localhost:{CHROME_PORT}/json", timeout=3)
        if r.status_code == 200:
            return {"status": "already_running", "message": "Chrome 调试端口已就绪"}
    except Exception:
        pass

    chrome_path = _find_chrome()
    if not chrome_path:
        return {"status": "chrome_not_found", "message": "未找到 Chrome，请手动安装"}

    profile_dir = Path.home() / ".tzzb_chrome_profile"
    profile_dir.mkdir(exist_ok=True)

    # 启动 Chrome（不等待退出）
    subprocess.Popen(
        [
            chrome_path,
            f"--remote-debugging-port={CHROME_PORT}",
            f"--user-data-dir={profile_dir}",
            CHROME_URL,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # 等待 Chrome 就绪
    for _ in range(15):
        try:
            r = httpx.get(f"http://localhost:{CHROME_PORT}/json", timeout=2)
            if r.status_code == 200:
                return {"status": "launched", "message": "Chrome 已启动，请在浏览器中完成登录"}
        except Exception:
            pass
        time.sleep(1)

    return {"status": "launch_failed", "message": "Chrome 启动超时，请检查防火墙/安全软件"}


def extract_cookies() -> dict[str, str] | None:
    """通过 CDP 提取 10jqka.com.cn 域的 Cookie"""
    try:
        r = httpx.get(f"http://localhost:{CHROME_PORT}/json", timeout=5)
        targets = r.json()
        if not targets:
            return None

        # 找一个有效的 page target
        page_target = next(
            (t for t in targets if t.get("type") == "page" and "devtoolsFrontendUrl" not in t.get("url", "")),
            targets[0],
        )
        ws_url = page_target["webSocketDebuggerUrl"]

        ws = websocket.WebSocket()
        ws.settimeout(10)
        ws.connect(ws_url)

        # 先启用 Network 域
        ws.send(json.dumps({"id": 1, "method": "Network.enable", "params": {}}))
        ws.recv()

        # 获取所有 Cookie
        ws.send(json.dumps({"id": 2, "method": "Network.getCookies", "params": {}}))
        response = json.loads(ws.recv())
        ws.close()

        cookies = response.get("result", {}).get("cookies", [])
        result = {}
        for c in cookies:
            if "10jqka.com.cn" in c.get("domain", "") and c["name"] in REQUIRED_COOKIES:
                result[c["name"]] = c["value"]

        if REQUIRED_COOKIES.issubset(result.keys()):
            _save_cookies(result)
            return result
        return None

    except Exception as e:
        return None


def get_cookies() -> dict[str, str] | None:
    """获取有效 Cookie，优先从本地加载"""
    return _load_cookies()


def get_login_status() -> LoginStatus:
    """检查登录状态"""
    cookies = _load_cookies()
    if cookies:
        return LoginStatus(
            logged_in=True,
            userid=cookies.get("userid", ""),
            cookie_count=len(cookies),
            extracted_at=json.loads(COOKIE_FILE.read_text(encoding="utf-8")).get("extracted_at", ""),
            message="已登录",
        )
    return LoginStatus(logged_in=False, message="未登录")


def login() -> dict:
    """登录流程：提取 Cookie → 保存 → 验证"""
    # 先尝试直接提取
    cookies = extract_cookies()
    if cookies:
        return {
            "status": "success",
            "message": f"Cookie 提取成功，userid={cookies.get('userid', '')[:6]}***",
            "cookies": {k: v[:6] + "***" for k, v in cookies.items()},
        }

    # 提取失败，尝试启动 Chrome
    launch_result = launch_chrome()
    if launch_result["status"] == "already_running":
        return {
            "status": "chrome_running_not_logged_in",
            "message": "Chrome 已在运行但未检测到登录 Cookie，请在 Chrome 中登录投资账本后重试",
        }
    elif launch_result["status"] in ("launched", "already_running"):
        return {
            "status": "waiting_login",
            "message": "Chrome 已启动，请在浏览器中完成登录后重试 tzzb_login",
            "launch": launch_result,
        }
    else:
        return {
            "status": "error",
            "message": launch_result["message"],
        }


def refresh_cookies() -> bool:
    """尝试刷新 Cookie（通过 upass 的 cookieRefresh 接口）"""
    cookies = _load_cookies()
    if not cookies:
        return False
    try:
        r = httpx.get(
            "https://upass.10jqka.com.cn/user/cookieRefresh",
            cookies=cookies,
            timeout=10,
        )
        return r.status_code == 200
    except Exception:
        return False


def clear() -> None:
    """清除本地 Cookie（登出）"""
    _clear_cookies()
