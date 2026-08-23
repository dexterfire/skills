#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vk_wall_poster.py — Universal, non-blocking VK wall poster designed for AI Agents (Hermes, Claude Code, etc.).

100% Non-interactive CLI:
- Never blocks on stdin/input()
- Instant diagnostics via --check (returns JSON or human-readable status)
- Instant automatic CDP-fallback if community token is missing, invalid, or refused
- Supports all browsers: Chrome, Yandex, Vivaldi, Firefox, Safari, Edge, Brave, Opera
"""

import argparse
import json
import os
import platform
import re
import subprocess
import sys
import time
import urllib.request
import urllib.parse
from typing import List, Optional, Tuple, Dict, Any

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    import io
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
        except Exception:
            pass

try:
    import websocket
except ImportError:
    websocket = None

try:
    import requests
except ImportError:
    requests = None


ENV_FILE_PATH = ".env"
STORAGE_KEY = "6287487:web_token:login:auth"


def load_env_vars() -> Dict[str, str]:
    env_vars = {}
    if os.path.exists(ENV_FILE_PATH):
        try:
            with open(ENV_FILE_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env_vars[k.strip()] = v.strip().strip("'\"")
        except Exception:
            pass
    return env_vars


def save_env_vars(updates: Dict[str, str]):
    lines = []
    if os.path.exists(ENV_FILE_PATH):
        try:
            with open(ENV_FILE_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            lines = []

    found = {k: False for k in updates}
    for i, line in enumerate(lines):
        line_clean = line.strip()
        if line_clean and not line_clean.startswith("#") and "=" in line_clean:
            k = line_clean.split("=", 1)[0].strip()
            if k in updates:
                lines[i] = f"{k}={updates[k]}\n"
                found[k] = True

    for k, val in updates.items():
        if not found[k]:
            lines.append(f"{k}={val}\n")

    with open(ENV_FILE_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)


def get_browser_catalog() -> List[Dict[str, Any]]:
    current_os = platform.system().lower()
    candidates = []

    if current_os == "windows":
        local_app = os.environ.get("LOCALAPPDATA", r"C:\Users\%USERNAME%\AppData\Local")
        prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        prog_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")

        candidates = [
            {"name": "Google Chrome", "path": os.path.join(prog_files, r"Google\Chrome\Application\chrome.exe"), "engine": "chromium"},
            {"name": "Google Chrome", "path": os.path.join(local_app, r"Google\Chrome\Application\chrome.exe"), "engine": "chromium"},
            {"name": "Google Chrome (x86)", "path": os.path.join(prog_files_x86, r"Google\Chrome\Application\chrome.exe"), "engine": "chromium"},
            {"name": "Yandex Browser", "path": os.path.join(prog_files, r"Yandex\YandexBrowser\Application\browser.exe"), "engine": "chromium"},
            {"name": "Yandex Browser", "path": os.path.join(local_app, r"Yandex\YandexBrowser\Application\browser.exe"), "engine": "chromium"},
            {"name": "Yandex Browser (x86)", "path": os.path.join(prog_files_x86, r"Yandex\YandexBrowser\Application\browser.exe"), "engine": "chromium"},
            {"name": "Vivaldi", "path": os.path.join(local_app, r"Vivaldi\Application\vivaldi.exe"), "engine": "chromium"},
            {"name": "Vivaldi", "path": os.path.join(prog_files, r"Vivaldi\Application\vivaldi.exe"), "engine": "chromium"},
            {"name": "Microsoft Edge", "path": os.path.join(prog_files_x86, r"Microsoft\Edge\Application\msedge.exe"), "engine": "chromium"},
            {"name": "Microsoft Edge", "path": os.path.join(prog_files, r"Microsoft\Edge\Application\msedge.exe"), "engine": "chromium"},
            {"name": "Brave Browser", "path": os.path.join(prog_files, r"BraveSoftware\Brave-Browser\Application\brave.exe"), "engine": "chromium"},
            {"name": "Brave Browser", "path": os.path.join(local_app, r"BraveSoftware\Brave-Browser\Application\brave.exe"), "engine": "chromium"},
            {"name": "Mozilla Firefox", "path": os.path.join(prog_files, r"Mozilla Firefox\firefox.exe"), "engine": "gecko"},
            {"name": "Mozilla Firefox (x86)", "path": os.path.join(prog_files_x86, r"Mozilla Firefox\firefox.exe"), "engine": "gecko"},
            {"name": "Mozilla Firefox", "path": os.path.join(local_app, r"Mozilla Firefox\firefox.exe"), "engine": "gecko"},
            {"name": "Opera", "path": os.path.join(local_app, r"Programs\Opera\launcher.exe"), "engine": "chromium"},
            {"name": "Opera GX", "path": os.path.join(local_app, r"Programs\Opera GX\launcher.exe"), "engine": "chromium"},
        ]
    elif current_os == "darwin":
        candidates = [
            {"name": "Google Chrome", "path": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "engine": "chromium"},
            {"name": "Yandex Browser", "path": "/Applications/Yandex.app/Contents/MacOS/Yandex", "engine": "chromium"},
            {"name": "Vivaldi", "path": "/Applications/Vivaldi.app/Contents/MacOS/Vivaldi", "engine": "chromium"},
            {"name": "Safari", "path": "/Applications/Safari.app/Contents/MacOS/Safari", "engine": "webkit"},
            {"name": "Mozilla Firefox", "path": "/Applications/Firefox.app/Contents/MacOS/firefox", "engine": "gecko"},
            {"name": "Microsoft Edge", "path": "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge", "engine": "chromium"},
            {"name": "Brave Browser", "path": "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser", "engine": "chromium"},
            {"name": "Opera", "path": "/Applications/Opera.app/Contents/MacOS/Opera", "engine": "chromium"},
            {"name": "Chromium", "path": "/Applications/Chromium.app/Contents/MacOS/Chromium", "engine": "chromium"},
        ]
    else:
        candidates = [
            {"name": "Google Chrome", "path": "/usr/bin/google-chrome", "engine": "chromium"},
            {"name": "Google Chrome Stable", "path": "/usr/bin/google-chrome-stable", "engine": "chromium"},
            {"name": "Yandex Browser", "path": "/usr/bin/yandex-browser", "engine": "chromium"},
            {"name": "Vivaldi", "path": "/usr/bin/vivaldi", "engine": "chromium"},
            {"name": "Mozilla Firefox", "path": "/usr/bin/firefox", "engine": "gecko"},
            {"name": "Chromium", "path": "/usr/bin/chromium", "engine": "chromium"},
            {"name": "Brave Browser", "path": "/usr/bin/brave-browser", "engine": "chromium"},
            {"name": "Microsoft Edge", "path": "/usr/bin/microsoft-edge-stable", "engine": "chromium"},
        ]

    existing = []
    seen_paths = set()
    for b in candidates:
        p = os.path.abspath(b["path"]) if os.path.exists(b["path"]) else b["path"]
        if os.path.exists(p) and p.lower() not in seen_paths:
            seen_paths.add(p.lower())
            existing.append({
                "name": b["name"],
                "path": p,
                "engine": b["engine"]
            })
    return existing


def is_port_alive(port: int, timeout: float = 1.5) -> bool:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=timeout)
        return True
    except Exception:
        return False


class VKTransport:
    def call_api(self, method: str, **params) -> Any:
        raise NotImplementedError

    def close(self):
        pass


class DirectTokenTransport(VKTransport):
    def __init__(self, token: str, api_version: str = "5.199"):
        self.token = token
        self.api_version = api_version

    def call_api(self, method: str, **params) -> Any:
        if not requests:
            raise RuntimeError("Библиотека requests не установлена (pip install requests)")
        headers = {"Authorization": f"Bearer {self.token}"}
        data = {k: str(v) for k, v in params.items()}
        data["v"] = self.api_version
        r = requests.post(f"https://api.vk.ru/method/{method}", headers=headers, data=data, timeout=20)
        r.raise_for_status()
        res = r.json()
        if "error" in res:
            err = res["error"]
            raise RuntimeError(f"VK API error {err.get('error_code')}: {err.get('error_msg')}")
        return res.get("response")


class CDPBrowserTransport(VKTransport):
    def __init__(self, port: int = 9223, browser_path: Optional[str] = None, user_data_dir: Optional[str] = None):
        if not websocket:
            raise RuntimeError("Библиотека websocket-client не установлена (pip install websocket-client)")
        self.port = port
        self.browser_path = browser_path
        self.user_data_dir = user_data_dir
        self.tab = self._ensure_vk_tab()
        self.ws = websocket.create_connection(self.tab["webSocketDebuggerUrl"], timeout=30)
        self.msg_id = 0

    def _ensure_browser_running(self):
        if is_port_alive(self.port):
            return
        
        catalog = get_browser_catalog()
        if self.browser_path:
            chosen_exe = self.browser_path
            chosen_name = "Custom Browser"
            chosen_engine = "chromium"
        elif catalog:
            chosen_exe = catalog[0]["path"]
            chosen_name = catalog[0]["name"]
            chosen_engine = catalog[0]["engine"]
        else:
            raise RuntimeError(f"Порт CDP {self.port} не активен и подходящий браузер не найден.")
        
        if chosen_engine == "gecko":
            args = [chosen_exe, f"--remote-debugging-port={self.port}", "https://vk.ru"]
        else:
            args = [chosen_exe, f"--remote-debugging-port={self.port}", "--remote-allow-origins=*", "--no-first-run"]
            if self.user_data_dir:
                args.append(f"--user-data-dir={self.user_data_dir}")
            args.append("https://vk.ru")

        print(f"[CDP-Auto] Запуск браузера {chosen_name} на порту {self.port}...")
        subprocess.Popen(args)
        for _ in range(25):
            time.sleep(1)
            if is_port_alive(self.port):
                print(f"[CDP-Auto] Браузер {chosen_name} успешно подключен.")
                return
        raise RuntimeError(f"Не удалось подключиться к браузеру {chosen_name} на порту {self.port}")

    def _ensure_vk_tab(self) -> dict:
        self._ensure_browser_running()
        tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json", timeout=5))
        vk_tabs = [t for t in tabs if ("vk.ru" in t.get("url", "") or "vk.com" in t.get("url", "")) and t.get("type") == "page"]
        if not vk_tabs:
            vk_tabs = [t for t in tabs if ("vk.ru" in t.get("url", "") or "vk.com" in t.get("url", ""))]
        if not vk_tabs:
            urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json/new?https://vk.ru", timeout=5)
            time.sleep(3)
            tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json", timeout=5))
            vk_tabs = [t for t in tabs if ("vk.ru" in t.get("url", "") or "vk.com" in t.get("url", ""))]
        if not vk_tabs:
            raise RuntimeError("В браузере нет открытой вкладки ВКонтакте.")
        return vk_tabs[0]

    def evaluate(self, js_expr: str) -> Any:
        self.msg_id += 1
        payload = {
            "id": self.msg_id,
            "method": "Runtime.evaluate",
            "params": {
                "expression": js_expr,
                "returnByValue": True,
                "awaitPromise": True
            }
        }
        self.ws.send(json.dumps(payload))
        while True:
            resp = json.loads(self.ws.recv())
            if resp.get("id") == self.msg_id:
                res = resp.get("result", {})
                if "exceptionDetails" in res:
                    raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
                return res.get("result", {}).get("value")

    def _execute_api_call(self, method: str, params: dict) -> Any:
        params_json = json.dumps({k: str(v) for k, v in params.items()})
        js = f"""
        (async () => {{
            try {{
                const raw = localStorage.getItem('{STORAGE_KEY}');
                let token = raw;
                try {{
                    const j = JSON.parse(raw);
                    token = j.token || j.access_token || raw;
                }} catch(e) {{}}
                
                const inputParams = {params_json};
                const p = new URLSearchParams();
                for (const [k, v] of Object.entries(inputParams)) {{
                    p.append(k, v);
                }}
                p.append('access_token', token);
                if (!p.has('v')) p.append('v', '5.199');
                
                const r = await fetch('https://api.vk.ru/method/{method}?' + p.toString(), {{
                    method: 'POST',
                    credentials: 'include'
                }});
                return await r.json();
            }} catch(err) {{
                return {{error: {{error_msg: err.toString(), error_code: -1}}}};
            }}
        }})()
        """
        return self.evaluate(js)

    def call_api(self, method: str, **params) -> Any:
        data = self._execute_api_call(method, params)
        if data and "error" in data and data["error"].get("error_code") == 5:
            print("[Auto-Refresh] Токен веб-сессии истек. Обновляем вкладку VK в браузере...")
            try:
                self.evaluate("window.location.reload()")
                time.sleep(3.5)
                data = self._execute_api_call(method, params)
            except Exception as e:
                print(f"[Auto-Refresh] Предупреждение: {e}")

        if not data:
            raise RuntimeError(f"Пустой ответ VK API для метода {method}")
        if "error" in data:
            err = data["error"]
            raise RuntimeError(f"VK API error {err.get('error_code')}: {err.get('error_msg')}")
        return data.get("response")

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def inspect_environment(port: int = 9223, token: Optional[str] = None) -> Dict[str, Any]:
    env_vars = load_env_vars()
    comm_token = token or env_vars.get("VK_COMMUNITY_TOKEN") or os.environ.get("VK_COMMUNITY_TOKEN")
    user_token = env_vars.get("VK_USER_TOKEN") or os.environ.get("VK_USER_TOKEN")
    group_id = env_vars.get("VK_GROUP_ID") or os.environ.get("VK_GROUP_ID") or "137821447"

    browsers = get_browser_catalog()
    cdp_alive = is_port_alive(port)
    is_windows = platform.system().lower() == "windows"
    is_headless = not os.environ.get("DISPLAY") and not is_windows and platform.system().lower() != "darwin"

    cdp_user = None
    if cdp_alive:
        try:
            temp_cdp = CDPBrowserTransport(port=port)
            u_info = temp_cdp.call_api("users.get")
            cdp_user = u_info[0] if u_info else None
            temp_cdp.close()
        except Exception:
            pass

    token_valid = False
    if comm_token:
        try:
            temp_token = DirectTokenTransport(comm_token)
            temp_token.call_api("groups.getById", group_id=group_id)
            token_valid = True
            temp_token.close()
        except Exception:
            pass

    recommended_mode = "NONE"
    if cdp_alive and cdp_user:
        recommended_mode = "CDP_ACTIVE"
    elif token_valid:
        recommended_mode = "DIRECT_TOKEN"
    elif browsers and not is_headless:
        recommended_mode = "CDP_AUTO_LAUNCH"
    else:
        recommended_mode = "CDP_FALLBACK"

    return {
        "os": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "browsers": browsers,
        "cdp_port": port,
        "cdp_alive": cdp_alive,
        "cdp_user": cdp_user,
        "comm_token_present": bool(comm_token),
        "comm_token_valid": token_valid,
        "user_token_present": bool(user_token),
        "group_id": group_id,
        "is_headless": is_headless,
        "recommended_mode": recommended_mode
    }


def print_diagnostic_report(diag: Dict[str, Any]):
    print("\n" + "=" * 68)
    print("[*] VK Wall Poster -- Диагностика окружения и статуса")
    print("=" * 68)
    print(f"  [+] Операционная система: {diag['os']}")
    
    if diag['browsers']:
        print(f"  [+] Обнаруженные браузеры в системе ({len(diag['browsers'])}):")
        for b in diag['browsers']:
            print(f"      - {b['name']}: {b['path']}")
    else:
        print(f"  [!] Браузеры в системе: не обнаружены (Headless/Server режим)")

    if diag['cdp_alive']:
        if diag['cdp_user']:
            print(f"  [+] Сессия браузера (CDP {diag['cdp_port']}): АКТИВНА (Пользователь: {diag['cdp_user'].get('first_name')} {diag['cdp_user'].get('last_name')}, ID {diag['cdp_user'].get('id')})")
        else:
            print(f"  [~] Сессия браузера (CDP {diag['cdp_port']}): Порт открыт, требуется вход в VK")
    else:
        print(f"  [i] Сессия браузера (CDP {diag['cdp_port']}): Не запущена (запустится автоматически через CDP-fallback)")

    if diag['comm_token_present']:
        status_tok = "ВАЛИДЕН" if diag['comm_token_valid'] else "ОШИБКА/ПРОТУХ (активен CDP-fallback)"
        print(f"  [+] Ключ сообщества (.env): Присутствует ({status_tok})")
    else:
        print(f"  [i] Ключ сообщества (.env): Не задан (автоматический CDP-fallback)")

    print("-" * 68)
    rec = diag['recommended_mode']
    if rec == "CDP_ACTIVE":
        print("--> Режим: [АВТО-CDP] Живая сессия браузера готова к мгновенной публикации.")
    elif rec == "DIRECT_TOKEN":
        print("--> Режим: [DIRECT-TOKEN] Прямой API-постинг через ключ сообщества.")
    elif rec in ("CDP_AUTO_LAUNCH", "CDP_FALLBACK"):
        b_name = diag['browsers'][0]['name'] if diag['browsers'] else 'Браузер'
        print(f"--> Режим: [CDP-FALLBACK] Автоматический постинг через сессию {b_name} (без ввода ключей).")
    print("=" * 68 + "\n")


class VKWallPublisher:
    def __init__(self,
                 primary_transport: VKTransport,
                 cdp_fallback_factory=None,
                 mode_label: str = "CDP"):
        self.transport = primary_transport
        self.cdp_fallback_factory = cdp_fallback_factory
        self.mode_label = mode_label

    @classmethod
    def auto_create(cls,
                    token: Optional[str] = None,
                    port: int = 9223,
                    browser_path: Optional[str] = None,
                    user_data_dir: Optional[str] = None) -> "VKWallPublisher":
        diag = inspect_environment(port=port, token=token)
        env_vars = load_env_vars()
        token = token or env_vars.get("VK_COMMUNITY_TOKEN") or os.environ.get("VK_COMMUNITY_TOKEN")

        def cdp_factory():
            return CDPBrowserTransport(port=port, browser_path=browser_path, user_data_dir=user_data_dir)

        # 1. If active CDP session is ready -> use it
        if diag["cdp_alive"] and diag["cdp_user"]:
            return cls(cdp_factory(), cdp_fallback_factory=None, mode_label="CDP (Живая сессия)")

        # 2. If valid direct token -> use it with CDP fallback
        if diag["comm_token_valid"] and not os.environ.get("VK_FORCE_CDP"):
            return cls(DirectTokenTransport(token), cdp_fallback_factory=cdp_factory, mode_label="Direct Token")

        # 3. If no token or invalid token -> AUTOMATIC CDP FALLBACK (launches local browser)
        try:
            return cls(cdp_factory(), cdp_fallback_factory=None, mode_label="CDP (Авто-запуск / Fallback)")
        except Exception as cdp_err:
            if token:
                return cls(DirectTokenTransport(token), cdp_fallback_factory=cdp_factory, mode_label="Direct Token")
            raise RuntimeError(f"Не удалось подключиться к сессии браузера: {cdp_err}") from cdp_err

    def resolve_target(self, target: Optional[str] = None) -> Tuple[int, bool, Dict[str, Any]]:
        env_vars = load_env_vars()
        if not target:
            env_group = env_vars.get("VK_GROUP_ID") or os.environ.get("VK_GROUP_ID")
            if env_group:
                target = env_group
            else:
                try:
                    user_info = self.transport.call_api("users.get")
                    user = user_info[0] if user_info else {}
                    return user.get("id", 0), False, user
                except Exception:
                    target = "glfire_streamer"

        target_clean = target.strip().rstrip("/").split("/")[-1]
        target_clean = re.sub(r"^(https?://)?(www\.)?(vk\.ru|vk\.com)/", "", target_clean)

        if target_clean.lstrip("-").isdigit():
            num = int(target_clean)
            if num < 0:
                gid = abs(num)
                g_info = self.transport.call_api("groups.getById", group_id=str(gid), fields="can_post,is_admin,admin_level")
                group = g_info["groups"][0] if ("groups" in g_info and g_info["groups"]) else g_info[0]
                return -gid, True, group
            else:
                try:
                    g_info = self.transport.call_api("groups.getById", group_id=str(num), fields="can_post,is_admin,admin_level")
                    group = g_info["groups"][0] if ("groups" in g_info and g_info["groups"]) else g_info[0]
                    return -num, True, group
                except Exception:
                    u_info = self.transport.call_api("users.get", user_ids=str(num))
                    user = u_info[0] if u_info else {}
                    return num, False, user

        if target_clean.startswith("public") or target_clean.startswith("club"):
            clean_num = re.sub(r"^(public|club)", "", target_clean)
            if clean_num.isdigit():
                gid = int(clean_num)
                g_info = self.transport.call_api("groups.getById", group_id=str(gid), fields="can_post,is_admin,admin_level")
                group = g_info["groups"][0] if ("groups" in g_info and g_info["groups"]) else g_info[0]
                return -gid, True, group

        if target_clean.startswith("id"):
            clean_num = target_clean[2:]
            if clean_num.isdigit():
                uid = int(clean_num)
                u_info = self.transport.call_api("users.get", user_ids=str(uid))
                user = u_info[0] if u_info else {}
                return uid, False, user

        try:
            resolved = self.transport.call_api("utils.resolveScreenName", screen_name=target_clean)
            if resolved and resolved.get("type") in ("group", "page", "event"):
                gid = int(resolved.get("object_id"))
                g_info = self.transport.call_api("groups.getById", group_id=str(gid), fields="can_post,is_admin,admin_level")
                group = g_info["groups"][0] if ("groups" in g_info and g_info["groups"]) else g_info[0]
                return -gid, True, group
            elif resolved and resolved.get("type") == "user":
                uid = int(resolved.get("object_id"))
                u_info = self.transport.call_api("users.get", user_ids=str(uid))
                user = u_info[0] if u_info else {}
                return uid, False, user
        except Exception:
            pass

        g_info = self.transport.call_api("groups.getById", group_ids=target_clean, fields="can_post,is_admin,admin_level")
        group = g_info["groups"][0] if ("groups" in g_info and g_info["groups"]) else g_info[0]
        return -int(group["id"]), True, group

    def upload_photo(self, photo_path: str, group_id: Optional[int] = None) -> str:
        if not os.path.exists(photo_path):
            raise FileNotFoundError(f"Файл изображения не найден: {photo_path}")
        if not requests:
            raise RuntimeError("requests library is required for photo upload (pip install requests)")

        transport = self.transport
        try:
            params = {"group_id": str(group_id)} if group_id else {}
            server_resp = transport.call_api("photos.getWallUploadServer", **params)
            upload_url = server_resp.get("upload_url")
        except Exception as e:
            if "error 27" in str(e).lower() and self.cdp_fallback_factory:
                print("[CDP-Fallback] Ключ сообщества не поддерживает загрузку фото (Error 27). Загружаем через CDP...")
                transport = self.cdp_fallback_factory()
                params = {"group_id": str(group_id)} if group_id else {}
                server_resp = transport.call_api("photos.getWallUploadServer", **params)
                upload_url = server_resp.get("upload_url")
            else:
                raise

        with open(photo_path, "rb") as f:
            resp = requests.post(upload_url, files={"photo": f}, timeout=30)
            resp.raise_for_status()
            upload_data = resp.json()

        save_params = {
            "photo": upload_data.get("photo"),
            "server": str(upload_data.get("server")),
            "hash": upload_data.get("hash")
        }
        if group_id:
            save_params["group_id"] = str(group_id)

        save_resp = transport.call_api("photos.saveWallPhoto", **save_params)
        saved_item = save_resp[0]
        return f"photo{saved_item['owner_id']}_{saved_item['id']}"

    def post(self,
             text: str,
             target: Optional[str] = None,
             photos: Optional[List[str]] = None,
             from_group: bool = True,
             publish_date: Optional[int] = None) -> Dict[str, Any]:
        owner_id, is_group, meta = self.resolve_target(target)
        group_id = abs(owner_id) if is_group else None

        attachments = []
        if photos:
            for p in photos:
                if p:
                    att = self.upload_photo(p, group_id=group_id)
                    attachments.append(att)

        post_params = {
            "owner_id": str(owner_id),
            "from_group": "1" if (is_group and from_group) else "0",
            "message": text
        }
        if attachments:
            post_params["attachments"] = ",".join(attachments)
        if publish_date:
            post_params["publish_date"] = str(publish_date)

        try:
            resp = self.transport.call_api("wall.post", **post_params)
        except Exception as e:
            if self.cdp_fallback_factory and any(err in str(e).lower() for err in ["error 38", "error 5", "ip address", "auth"]):
                print(f"[CDP-Fallback] Прямой токен вернул ошибку ({e}). Автоматически публикуем через CDP браузера...")
                cdp_transport = self.cdp_fallback_factory()
                self.transport = cdp_transport
                resp = cdp_transport.call_api("wall.post", **post_params)
            else:
                raise

        post_id = resp.get("post_id")
        return {
            "post_id": post_id,
            "owner_id": owner_id,
            "is_group": is_group,
            "target_meta": meta,
            "url": f"https://vk.ru/wall{owner_id}_{post_id}"
        }

    def close(self):
        self.transport.close()


def parse_delay_to_timestamp(delay_str: str) -> int:
    delay_str = delay_str.strip().lower()
    now = int(time.time())
    m = re.match(r"^(\d+)\s*([smhd])$", delay_str)
    if not m:
        raise ValueError(f"Неверный формат задержки: '{delay_str}'. Примеры: '15m', '1h', '24h'")
    val, unit = int(m.group(1)), m.group(2)
    mult = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
    return now + (val * mult)


def main():
    parser = argparse.ArgumentParser(
        description="Universal VK Wall Poster -- умный неблокирующий авто-постинг в ВК для AI-агентов.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--check", "--status", action="store_true", help="Провести диагностику окружения")
    parser.add_argument("--target", type=str, default="glfire_streamer", help="Группа или пользователь")
    parser.add_argument("--text", type=str, help="Текст публикации")
    parser.add_argument("--file", type=str, help="Файл с текстом публикации")
    parser.add_argument("--photo", type=str, nargs="+", help="Изображения (до 10)")
    parser.add_argument("--publish-date", type=int, help="Unix timestamp")
    parser.add_argument("--delay", type=str, help="Относительная задержка ('15m', '1h')")
    parser.add_argument("--as-user", action="store_true", help="Опубликовать от имени пользователя")
    parser.add_argument("--token", type=str, help="Прямой токен доступа")
    parser.add_argument("--port", type=int, default=9223, help="Порт CDP")
    parser.add_argument("--user-data-dir", type=str, help="Каталог профиля браузера")
    parser.add_argument("--browser-path", type=str, help="Путь к браузеру")

    args = parser.parse_args()

    if args.check:
        diag = inspect_environment(port=args.port, token=args.token)
        print_diagnostic_report(diag)
        try:
            publisher = VKWallPublisher.auto_create(token=args.token, port=args.port, browser_path=args.browser_path, user_data_dir=args.user_data_dir)
            owner_id, is_group, meta = publisher.resolve_target(args.target)
            if is_group:
                print(f"Целевое сообщество: «{meta.get('name')}» (ID: {meta.get('id')})")
                print(f"Права на публикацию (can_post): {bool(meta.get('can_post'))} | Admin Level: {meta.get('admin_level')}")
            else:
                print(f"Целевой пользователь: «{meta.get('first_name')} {meta.get('last_name')}» (ID: {meta.get('id')})")
            print(f"Статус: [+] ПОЛНОСТЬЮ ГОТОВ К РАБОТЕ\n")
            publisher.close()
        except Exception as e:
            print(f"Статус готовности: [!] Требуется настройка ({e})\n")
        return

    user_data = args.user_data_dir
    if not user_data and platform.system().lower() == "windows":
        default_profile = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data Mikhail")
        if os.path.exists(default_profile):
            user_data = default_profile

    publisher = VKWallPublisher.auto_create(
        token=args.token,
        port=args.port,
        browser_path=args.browser_path,
        user_data_dir=user_data
    )

    try:
        text = args.text
        if args.file:
            with open(args.file, "r", encoding="utf-8") as f:
                text = f.read().strip()

        if not text:
            print("Ошибка: Текст публикации не указан.", file=sys.stderr)
            sys.exit(1)

        publish_date = args.publish_date
        if args.delay:
            publish_date = parse_delay_to_timestamp(args.delay)

        result = publisher.post(
            text=text,
            target=args.target,
            photos=args.photo,
            from_group=not args.as_user,
            publish_date=publish_date
        )

        post_id = result["post_id"]
        if publish_date:
            from datetime import datetime
            dt_str = datetime.fromtimestamp(publish_date).strftime("%d.%m.%Y в %H:%M:%S")
            print(f"[+] УСПЕХ: Пост #{post_id} запланирован на {dt_str}!")
        else:
            print(f"[+] УСПЕХ: Пост #{post_id} опубликован!")
        print(f"--> Ссылка: {result['url']}")

    finally:
        publisher.close()


if __name__ == "__main__":
    main()
