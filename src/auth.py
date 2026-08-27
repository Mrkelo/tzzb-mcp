"""Cookie 提取与认证管理 — 基于 Chrome CDP

核心原则：绝不杀用户 Chrome，使用独立 Profile 隔离，纯 Python 零 Node.js 依赖。
"""

from __future__ import annotations

import json
import socket
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

import websocket

from .models import LoginStatus

COOKIE_FILE = Path.home() / ".tzzb_cookies.json"
REQUIRED_COOKIES = {"userid", "ticket", "user"}
TZZB_URL = "https://tzzb.10jqka.com.cn/pc/index.html#/unlogin"
CDP_PORT = 9222
CHROME_PROFILE = Path.home() / ".tzzb_chrome_profile"

_ws: websocket.WebSocket | None = None
_msg_id: int = 0
_cdp_lock = threading.Lock()


# ============================================================
# Chrome 生命周期管理
# ============================================================


def _check_port(port: int) -> bool:
    """检测端口是否被占用"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()
        return result == 0
    except Exception:
        return False


def _find_chrome() -> str | None:
    """查找系统中 Chrome 可执行文件"""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        str(Path.home() / "AppData/Local/Google/Chrome/Application/chrome.exe"),
    ]
    for path in candidates:
        if Path(path).exists():
            return path
    try:
        result = subprocess.run(
            ["where", "chrome"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split("\n")[0]
    except Exception:
        pass
    return None


def _launch_chrome() -> bool:
    """启动 Chrome 调试实例（独立 Profile，绝不杀用户 Chrome）"""
    chrome_path = _find_chrome()
    if not chrome_path:
        return False

    CHROME_PROFILE.mkdir(parents=True, exist_ok=True)

    creationflags = 0
    if hasattr(subprocess, "DETACHED_PROCESS"):
        creationflags |= subprocess.DETACHED_PROCESS
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        creationflags |= subprocess.CREATE_NO_WINDOW

    subprocess.Popen(
        [
            chrome_path,
            f"--remote-debugging-port={CDP_PORT}",
            f"--user-data-dir={CHROME_PROFILE}",
            "--remote-allow-origins=*",
            "--no-first-run",
            "--no-default-browser-check",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )

    for _ in range(30):
        time.sleep(1)
        if _check_port(CDP_PORT):
            return True
    return False


# ============================================================
# CDP 连接管理
# ============================================================


def _reset_connection() -> None:
    """安全关闭旧 WebSocket 连接，重置全局状态"""
    global _ws
    if _ws:
        try:
            _ws.close()
        except Exception:
            pass
        _ws = None


def _ensure_connection() -> None:
    """确保 Chrome 调试实例在运行，且 CDP WebSocket 连接有效

    调用方必须持有 _cdp_lock。
    """
    global _ws

    if _ws is not None:
        try:
            _ws.ping()
            return
        except Exception:
            _reset_connection()

    if not _check_port(CDP_PORT):
        if not _launch_chrome():
            raise RuntimeError("无法启动 Chrome 调试实例")

    _cdp_connect()


def _get_page_ws_url() -> str:
    """获取任意页面目标的 WebSocket URL"""
    resp = urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json")
    targets = json.loads(resp.read())

    for t in targets:
        if t.get("type") == "page":
            return t["webSocketDebuggerUrl"]

    raise RuntimeError("Chrome 中没有可用的页面目标")


def _wait_for_page_load(timeout: int = 15) -> None:
    """等待页面加载完成，通过 Runtime.evaluate 轮询检测

    页面加载完成后，hexin-v 反爬机制才会在 localStorage 中生成标头，
    fetch 请求才能正确携带。固定 sleep 2 秒可能不够，导致概率性空数据。

    使用 Runtime.evaluate 轮询 document.readyState 而非监听 CDP 事件，
    避免事件竞态（ebd 残留的旧 loadEventFired 可能被误匹配）。
    """
    global _msg_id

    # 1. 导航到 tzzb 页面
    _msg_id += 1
    nav_msg = {
        "id": _msg_id,
        "method": "Page.navigate",
        "params": {"url": "https://tzzb.10jqka.com.cn/pc/index.html"},
    }
    _ws.send(json.dumps(nav_msg))

    # 等待 navigate 响应（消费掉，避免干扰后续轮询）
    try:
        _ws.settimeout(5)
        while True:
            raw = _ws.recv()
            parsed = json.loads(raw)
            if parsed.get("id") == _msg_id:
                break
    except Exception:
        pass

    # 2. 轮询 Runtime.evaluate 检测页面是否就绪
    #    使用 eval 检查 document.readyState，比监听事件更可靠
    check_expr = "(function(){return document.readyState==='complete'?1:0})()"
    deadline = time.time() + timeout
    while time.time() < deadline:
        _msg_id += 1
        eval_msg = {
            "id": _msg_id,
            "method": "Runtime.evaluate",
            "params": {
                "expression": check_expr,
                "returnByValue": True,
                "awaitPromise": False,
            },
        }
        _ws.send(json.dumps(eval_msg))

        try:
            _ws.settimeout(3)
            while True:
                raw = _ws.recv()
                parsed = json.loads(raw)
                if parsed.get("id") == _msg_id:
                    value = parsed.get("result", {}).get("result", {}).get("value", 0)
                    if value == 1:
                        # 页面就绪，再等 1 秒确保反爬标头生成
                        time.sleep(1)
                        return
                    break
        except websocket.WebSocketTimeoutException:
            pass
        time.sleep(0.5)

    # fallback：超时则退回到固定 sleep
    time.sleep(3)


def _cdp_connect() -> None:
    """连接到页面目标并导航到 tzzb 域名"""
    global _ws, _msg_id

    _reset_connection()

    ws_url = _get_page_ws_url()
    _ws = websocket.create_connection(ws_url, timeout=10)
    _msg_id = 0

    # 启用 Page 域并导航到 tzzb 页面
    _cdp_send("Page.enable")
    # 等待页面完全加载（_wait_for_page_load 内部发送 Page.navigate 并监听 loadEventFired）
    # 固定 sleep 2 秒可能导致页面未加载完成就开始发请求，概率性返回空数据
    _wait_for_page_load(timeout=15)


def _cdp_send(method: str, params: dict | None = None) -> dict:
    """发送 CDP 命令并返回解析后的结果（底层实现，不做重连）

    Chrome 会持续推送事件消息，需要循环 recv 直到收到匹配 id 的响应。
    """
    global _msg_id

    _msg_id += 1
    msg = {"id": _msg_id, "method": method, "params": params or {}}
    _ws.send(json.dumps(msg))

    while True:
        raw = _ws.recv()
        parsed = json.loads(raw)
        if parsed.get("id") == _msg_id:
            return parsed


def _cdp_send_safe(method: str, params: dict | None = None) -> dict:
    """发送 CDP 命令，连接断开时自动重连重试一次

    使用全局锁保证 _ws 和 _msg_id 的线程安全，
    防止 agent 并行调用多个 MCP 工具时互相抢响应。
    """
    with _cdp_lock:
        _ensure_connection()

        try:
            return _cdp_send(method, params)
        except (websocket.WebSocketException, ConnectionError, OSError):
            _reset_connection()
            _ensure_connection()
            try:
                return _cdp_send(method, params)
            except Exception:
                _reset_connection()
                raise


def cdp_evaluate(expression: str) -> dict:
    """在浏览器页面中执行 JavaScript 并返回结果

    供 client.py 使用，通过 Runtime.evaluate 在浏览器内执行 fetch。
    自带断线重连机制。
    """
    return _cdp_send_safe(
        "Runtime.evaluate",
        {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True,
        },
    )


def cdp_get_cookies() -> dict[str, str]:
    """通过 CDP 获取 10jqka 域名的 Cookie，自带断线重连"""
    result = _cdp_send_safe(
        "Network.getCookies", {"urls": ["https://tzzb.10jqka.com.cn"]}
    )
    cookies = result.get("result", {}).get("cookies", [])

    extracted: dict[str, str] = {}
    for c in cookies:
        if "10jqka.com.cn" in c.get("domain", "") and c["name"] in REQUIRED_COOKIES:
            extracted[c["name"]] = c["value"]

    return extracted if REQUIRED_COOKIES.issubset(extracted.keys()) else {}


# ============================================================
# Cookie 持久化
# ============================================================


def _load_cookies() -> dict[str, str] | None:
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
    data = {
        **cookies,
        "extracted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source": "cdp",
    }
    COOKIE_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _clear_cookies() -> None:
    COOKIE_FILE.unlink(missing_ok=True)


# ============================================================
# 公开 API
# ============================================================


def get_cookies() -> dict[str, str] | None:
    return _load_cookies()


def get_login_status() -> LoginStatus:
    cookies = _load_cookies()
    if cookies:
        raw = json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
        return LoginStatus(
            logged_in=True,
            userid=cookies.get("userid", ""),
            cookie_count=len(cookies),
            extracted_at=raw.get("extracted_at", ""),
            message="已登录",
        )
    return LoginStatus(logged_in=False, message="未登录")


def login(timeout: int = 120) -> dict:
    """登录流程：确保 CDP 可用 → 提取 Cookie → 等待用户登录

    策略：
    1. 确保 Chrome 在 9222 端口运行（连接或启动）
    2. 检查已有 Cookie 是否有效
    3. 无效则导航到登录页等待用户手动登录
    """
    try:
        # 确保 Chrome 运行
        if not _check_port(CDP_PORT):
            if not _launch_chrome():
                return {
                    "status": "error",
                    "message": "无法启动 Chrome，请安装 Chrome 并手动启动",
                }

        # 策略1：已有有效 Cookie
        existing = cdp_get_cookies()
        if existing:
            _save_cookies(existing)
            return {
                "status": "success",
                "message": f"Cookie 有效，userid={existing['userid'][:6]}***",
                "cookies": {k: v[:6] + "***" for k, v in existing.items()},
            }

        # 策略2：导航到登录页等待用户手动登录
        _cdp_send_safe("Page.navigate", {"url": TZZB_URL})

        for _ in range(timeout // 2):
            time.sleep(2)
            found = cdp_get_cookies()
            if found:
                _save_cookies(found)
                return {
                    "status": "success",
                    "message": f"登录成功，userid={found['userid'][:6]}***",
                    "cookies": {k: v[:6] + "***" for k, v in found.items()},
                }

        return {
            "status": "timeout",
            "message": f"等待登录超时（{timeout}秒），请在浏览器中完成登录后重试",
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


def close() -> None:
    global _ws
    with _cdp_lock:
        try:
            if _ws:
                _ws.close()
        except Exception:
            pass
        finally:
            _ws = None


def clear() -> None:
    _clear_cookies()