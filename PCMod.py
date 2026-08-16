import os
import sys
import time
import json
import urllib.request
import urllib.error
import urllib.parse
import ssl
import subprocess
import re
import hashlib
import ftplib
import threading
import webview
from datetime import datetime

# Ensure data directory exists
OS_NAME = sys.platform
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
BIN_DIR = os.path.join(BASE_DIR, "bin")
CMD_DIR = os.path.join(BASE_DIR, "cmd")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "indexes"), exist_ok=True)

INIT_LOG = os.path.join(DATA_DIR, "init.log")

def log_init(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    print(entry)
    try:
        with open(INIT_LOG, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception:
        pass

log_init("=== PCMod Client Starting ===")
log_init(f"OS: {OS_NAME} | Base Dir: {BASE_DIR}")

# Dynamic Windows Console Title, Icon & Taskbar Grouping setup
if OS_NAME == "win32":
    try:
        import ctypes
        import ctypes.wintypes

        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x00000010
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1
        GCLP_HICON = -14
        GCLP_HICONSM = -34

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        # Explicit AppUserModelID to group console window and client GUI into 1 taskbar icon stack
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PCMod.Client.1.0")
            log_init("SetCurrentProcessExplicitAppUserModelID set: PCMod.Client.1.0")
        except Exception as e:
            log_init(f"SetCurrentProcessExplicitAppUserModelID warning: {e}")

        console_hwnd = kernel32.GetConsoleWindow()
        if console_hwnd:
            kernel32.SetConsoleTitleW("PCMod Console")
            icon_path = os.path.join(DATA_DIR, "icons", "icon.ico")
            if os.path.exists(icon_path):
                hicon_small = user32.LoadImageW(None, icon_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
                hicon_big = user32.LoadImageW(None, icon_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
                if hicon_small:
                    user32.SendMessageW(console_hwnd, WM_SETICON, ICON_SMALL, hicon_small)
                if hicon_big:
                    user32.SendMessageW(console_hwnd, WM_SETICON, ICON_BIG, hicon_big)
                log_init("Console window icon applied successfully")
    except Exception as e:
        log_init(f"Console title/icon setup error: {e}")

def update_console_title(username):
    if OS_NAME == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW(f"PCMod Console - {username}")
            log_init(f"Console title updated for user: {username}")
        except Exception:
            pass

SETTINGS_FILE = os.path.join(BASE_DIR, "settings.txt")

def get_default_settings():
    return {
        "shortcut": "0",
        "autoserver": "0",
        "log-logins": "0",
        "lite": "0",
        "showconsole": "1",
        "pack": "2-5-x",
        "memory": "4096",
        "username": ""
    }

def read_settings():
    settings = get_default_settings()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip().lower() != "password":  # Security: never read passwords from settings.txt
                            settings[k.strip()] = v.strip()
            log_init(f"Read settings.txt successfully: {settings}")
        except Exception as e:
            log_init(f"Error reading settings.txt: {e}")
    else:
        log_init("settings.txt does not exist, using default settings")
    return settings

def write_settings(settings):
    try:
        lines = []
        for k, v in settings.items():
            if k.lower() == "password": # Security: NEVER store passwords in settings.txt
                continue
            lines.append(f"{k}={v}\n")
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)
        log_init(f"Wrote settings.txt successfully (sanitized passwords)")

        if OS_NAME == "win32" and "showconsole" in settings:
            try:
                import ctypes
                hwnd = ctypes.windll.kernel32.GetConsoleWindow()
                if hwnd:
                    show = 1 if str(settings["showconsole"]).strip() in ["1", "true", "True"] else 0
                    ctypes.windll.user32.ShowWindow(hwnd, show)
            except Exception as e:
                log_init(f"ShowWindow error: {e}")
    except Exception as e:
        log_init(f"Error writing settings.txt: {e}")

init_settings = read_settings()
if OS_NAME == "win32" and str(init_settings.get("showconsole", "1")).strip() in ["0", "false", "False"]:
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass

def get_pack_name():
    s = read_settings()
    if s.get("pack"):
        return s.get("pack")
    pack_txt = os.path.join(DATA_DIR, "pack.txt")
    if os.path.exists(pack_txt):
        try:
            with open(pack_txt, "r", encoding="utf-8") as f:
                val = f.read().strip()
                if val:
                    return val
        except Exception:
            pass
    return "2-5-x"

def read_version_indexes(pack_name):
    launcher_ver = "1.2a"
    pack_ver = "2.5.3a"

    version_files = [
        os.path.join(DATA_DIR, "indexes", "version"),
        os.path.join(DATA_DIR, "indexes", "version.tmp")
    ]

    for vfile in version_files:
        if os.path.exists(vfile):
            try:
                with open(vfile, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        parts = line.strip().split(";")
                        if len(parts) >= 2:
                            key = parts[0].strip()
                            ver = parts[1].strip()
                            if key == "Launcher":
                                launcher_ver = ver
                            elif key == pack_name:
                                pack_ver = ver
            except Exception as e:
                log_init(f"Error reading version file {vfile}: {e}")

    log_init(f"Resolved Versions: Launcher={launcher_ver} | Pack ({pack_name})={pack_ver}")
    return launcher_ver, pack_ver

def get_offline_uuid(username):
    s = f"OfflinePlayer:{username}"
    md5 = hashlib.md5(s.encode('utf-8')).digest()
    md5_bytearray = bytearray(md5)
    md5_bytearray[6] &= 0x0f
    md5_bytearray[6] |= 0x30
    md5_bytearray[8] &= 0x3f
    md5_bytearray[8] |= 0x80
    hex_str = md5_bytearray.hex()
    return f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:]}"

USER_INFO = {
    "username": "",
    "uuid": "",
    "auth_token": "",
    "valid": False
}

def rot13_5(text):
    res = []
    for ch in text:
        if 'a' <= ch <= 'z':
            res.append(chr((ord(ch) - ord('a') + 13) % 26 + ord('a')))
        elif 'A' <= ch <= 'Z':
            res.append(chr((ord(ch) - ord('A') + 13) % 26 + ord('A')))
        elif '0' <= ch <= '9':
            res.append(chr((ord(ch) - ord('0') + 5) % 10 + ord('0')))
        else:
            res.append(ch)
    return "".join(res)

def generate_auth_file_xcode(username, password):
    if not username or not password:
        return ""
    log_init(f"Checking User Length: {len(username)}")
    log_init(f"Authorizing User ({username})...")

    auth_file = os.path.join(DATA_DIR, "indexes", "auth")
    xcode_exe = os.path.join(BIN_DIR, "xcode.exe")

    if os.path.exists(xcode_exe):
        try:
            # Matching settings.bat: echo.%user%|bin\xcode.exe data\indexes\auth >nul
            proc = subprocess.Popen([xcode_exe, auth_file], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0x08000000 if OS_NAME=="win32" else 0)
            input_data = f"{username}\r\n{password}\r\n".encode('utf-8')
            proc.communicate(input=input_data, timeout=2)
            log_init(f"Wrote xcode auth file to {auth_file}")
        except Exception as e:
            log_init(f"xcode execution error: {e}")

    # Read token from data/indexes/auth
    if os.path.exists(auth_file):
        try:
            with open(auth_file, "r", encoding="utf-8", errors="ignore") as f:
                token = f.read().strip()
                if token:
                    log_init(f"Token read from data/indexes/auth: {token}")
                    return token
        except Exception as e:
            log_init(f"Error reading auth file: {e}")

    token = hashlib.md5((username + password).encode('utf-8')).hexdigest()
    try:
        with open(auth_file, "w", encoding="utf-8") as f:
            f.write(token)
    except Exception:
        pass
    log_init(f"Fallback MD5 auth token generated: {token}")
    return token

def get_xcode_auth(username, password):
    return generate_auth_file_xcode(username, password)

def get_uuid_tool_uuid(username):
    if not username:
        return ""
    log_init(f"Resolving Mojang UUID for user: {username}")
    uuid_jar = os.path.join(BIN_DIR, "uuid-tool-1.0.jar")
    if os.path.exists(uuid_jar):
        try:
            proc = subprocess.Popen(["java", "-jar", uuid_jar], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0x08000000 if OS_NAME=="win32" else 0)
            input_data = f"{username}\r\n".encode('utf-8')
            out, err = proc.communicate(input=input_data, timeout=2)
            out_str = out.decode('utf-8', errors='ignore').strip()
            match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', out_str, re.I)
            if match:
                uuid_val = match.group(0)
                log_init(f"uuid-tool resolved UUID: {uuid_val}")
                return uuid_val
        except Exception as e:
            log_init(f"uuid-tool execution error: {e}")
    offline_uuid = get_offline_uuid(username)
    log_init(f"Fallback offline UUID generated: {offline_uuid}")
    return offline_uuid

def load_user_info():
    s = read_settings()
    u = s.get("username", "")
    p = s.get("password", "")
    if u:
        USER_INFO["username"] = u
        USER_INFO["auth_token"] = get_xcode_auth(u, p)
        USER_INFO["uuid"] = get_uuid_tool_uuid(u)
        USER_INFO["valid"] = True
        update_console_title(u)
        log_init(f"Loaded user info successfully: User={u} | UUID={USER_INFO['uuid']}")

load_user_info()

def get_versions_list():
    packs_dir = os.path.join(DATA_DIR, "packs")
    versions = []
    if os.path.exists(packs_dir):
        try:
            for d in sorted(os.listdir(packs_dir)):
                p = os.path.join(packs_dir, d)
                if os.path.isdir(p):
                    versions.append({"name": d, "path": p})
        except Exception as e:
            log_init(f"Error listing packs: {e}")
    if not versions:
        versions = [{"name": "2-5-x", "path": os.path.join(DATA_DIR, "packs", "2-5-x")}]
    log_init(f"Available versions list: {[v['name'] for v in versions]}")
    return versions

class Api:
    def __init__(self):
        self._window = None

    def set_window(self, window):
        self._window = window

    def init_launcher(self, *args, **kwargs):
        log_init("init_launcher invoked by frontend UI")
        s = read_settings()
        pack = get_pack_name()
        modcount = self.get_mod_count()
        launcher_ver, pack_ver = read_version_indexes(pack)
        log_init(f"Launcher State: Pack={pack} | LauncherVer={launcher_ver} | PackVer={pack_ver} | ModCount={modcount} | Username={s.get('username', '')}")

        return {
            "user": s.get("username", ""),
            "settings": {
                "shortcut": "1" if str(s.get("shortcut")).strip() in ["1", "true", "True"] else "0",
                "autoserver": "1" if str(s.get("autoserver")).strip() in ["1", "true", "True"] else "0",
                "log_logins": "1" if str(s.get("log-logins", s.get("log_logins", "0"))).strip() in ["1", "true", "True"] else "0",
                "log-logins": "1" if str(s.get("log-logins", s.get("log_logins", "0"))).strip() in ["1", "true", "True"] else "0",
                "lite": "1" if str(s.get("lite", s.get("litemode", "0"))).strip() in ["1", "true", "True"] else "0",
                "showconsole": "1" if str(s.get("showconsole")).strip() in ["1", "true", "True"] else "0",
                "memory": str(s.get("memory", s.get("maxram", "4096"))),
                "pack": pack
            },
            "modcount": str(modcount),
            "launcher_version": launcher_ver,
            "pack_version": pack_ver,
            "versions_list": get_versions_list(),
            "online_players": "Loading...",
            "news_url": "news.html"
        }

    def get_settings(self, *args, **kwargs):
        log_init("get_settings invoked")
        return read_settings()

    def save_settings(self, *args, **kwargs):
        log_init(f"save_settings invoked: args={args}, kwargs={kwargs}")
        if args and isinstance(args[0], dict):
            s = args[0]
        else:
            s = read_settings()
        current = read_settings()
        current.update(s)
        write_settings(current)
        load_user_info()
        return True

    def save_settings_btn(self, *args, **kwargs):
        log_init("save_settings_btn invoked")
        return self.save_settings(*args, **kwargs)

    def set_setting(self, *args, **kwargs):
        if len(args) >= 2:
            k, v = args[0], args[1]
            s = read_settings()
            s[str(k)] = str(v)
            write_settings(s)
            log_init(f"Setting changed: {k} = {v}")
        return True

    def set_lite_mode(self, *args, **kwargs):
        val = args[0] if args else "0"
        log_init(f"set_lite_mode invoked: {val}")
        s = read_settings()
        s["lite"] = str(val)
        write_settings(s)
        return True

    def set_memory(self, *args, **kwargs):
        val = args[0] if args else "4096"
        log_init(f"set_memory invoked: {val} MB")
        s = read_settings()
        s["memory"] = str(val)
        write_settings(s)
        return True

    def set_version_select(self, *args, **kwargs):
        val = args[0] if args else ""
        if " " in str(val):
            val = str(val).split(" ", 1)[1]
        log_init(f"set_version_select invoked: Selected pack={val}")
        s = read_settings()
        s["pack"] = str(val)
        write_settings(s)
        return True

    def get_mod_count(self, *args, **kwargs):
        pack = get_pack_name()
        mods_dir = os.path.join(DATA_DIR, "packs", pack, "mods")
        if os.path.exists(mods_dir):
            try:
                count = sum(1 for f in os.listdir(mods_dir) if f.endswith(".jar") or f.endswith(".zip") or f.endswith(".disabled"))
                log_init(f"Counted {count} mods in {mods_dir}")
                return count
            except Exception as e:
                log_init(f"Error counting mods: {e}")
        return 0

    def open_modlist(self, *args, **kwargs):
        log_init("open_modlist invoked")
        settings_bat = os.path.join(CMD_DIR, "settings.bat")
        if os.path.exists(settings_bat):
            try:
                if OS_NAME == "win32":
                    subprocess.run(["cmd.exe", "/c", settings_bat, "modlist"], cwd=BASE_DIR, timeout=5)
                else:
                    subprocess.run(["bash", settings_bat, "modlist"], cwd=BASE_DIR, timeout=5)
            except Exception as e:
                log_init(f"Error running settings.bat modlist: {e}")

        modlist_html = os.path.join(DATA_DIR, "pages", "modlist.html")
        if os.path.exists(modlist_html):
            url = f"file://{os.path.abspath(modlist_html)}"
            log_init(f"Opening modlist HTML page: {url}")
            try:
                webview.create_window("PCMod Modlist", url, width=820, height=520, resizable=True)
            except Exception as e:
                log_init(f"Opening modlist in default browser: {e}")
                import webbrowser
                webbrowser.open(url)
        else:
            pack = get_pack_name()
            mods_dir = os.path.join(DATA_DIR, "packs", pack, "mods")
            os.makedirs(mods_dir, exist_ok=True)
            log_init(f"modlist.html not found, fallback opening mods folder: {mods_dir}")
            if OS_NAME == "win32":
                os.startfile(mods_dir)
            else:
                subprocess.Popen(["open" if OS_NAME=="darwin" else "xdg-open", mods_dir])
        return True

    def open_link(self, *args, **kwargs):
        url = args[0] if args else "http://pcmod.ddns.me"
        log_init(f"Opening browser URL: {url}")
        import webbrowser
        webbrowser.open(url)
        return True

    def open_web(self, *args, **kwargs):
        site = args[0] if args else "pcmod"
        url = "http://pcmod.ddns.me"
        if site == "discord":
            url = "https://discord.gg/AJaVhvR"
        elif site == "auth":
            url = "http://pcmod.ddns.me/account"
        log_init(f"open_web invoked for site '{site}' -> {url}")
        return self.open_link(url)

    def get_news_url(self, *args, **kwargs):
        remote_url = "https://pcmod.ddns.me/updates/news.html"
        local_news_path = os.path.join(DATA_DIR, "pages", "news.html")
        os.makedirs(os.path.join(DATA_DIR, "pages"), exist_ok=True)
        log_init(f"Fetching news from remote URL: {remote_url}")
        try:
            req = urllib.request.Request(remote_url, headers={'User-Agent': 'Mozilla/5.0'})
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=1.5, context=ctx) as resp:
                content = resp.read().decode('utf-8', errors='ignore')
                if content and len(content) > 10:
                    try:
                        with open(local_news_path, "w", encoding="utf-8") as f:
                            f.write(content)
                        log_init("Cached news.html successfully")
                    except Exception as e:
                        log_init(f"Failed to cache news.html: {e}")
                    return remote_url
        except Exception as e:
            log_init(f"Unable to fetch online news ({e}); using local news page")

        if os.path.exists(local_news_path):
            log_init("Using local cached news.html")
            return "news.html"
        return "news.html"

    def get_players_online(self, *args, **kwargs):
        pack = get_pack_name()
        url = f"http://pcmod.ddns.me/players/list-{pack}"
        log_init(f"Fetching online players list from batch-specified URL: {url}")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=1.5, context=ctx) as response:
                text = response.read().decode('utf-8', errors='ignore').strip()
                players = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("<")]
                log_init(f"Online players response parsed: {len(players)} players ({players})")
                if players:
                    html_lines = "<br>".join([f"• {p}" for p in players])
                    return {"status": f"{len(players)} Online", "players": players, "players_html": html_lines}
                return {"status": "No Players Online", "players": [], "players_html": "No players online"}
        except Exception as e:
            log_init(f"Online players request exception: {e}")
            return {"status": "Server Offline", "players": [], "players_html": "Server Offline"}

    def refresh_players(self, *args, **kwargs):
        log_init("refresh_players invoked")
        res = self.get_players_online()
        return res.get("players_html", res.get("status", "No players online"))

    def login(self, *args, **kwargs):
        username = args[0] if len(args) > 0 else ""
        password = args[1] if len(args) > 1 else ""
        log_init(f"login API invoked for user: {username}")
        res = self.verify_login(username, password)
        return {
            "status": "success" if res.get("success") else "failed",
            "auth": res.get("message", "auth_failed")
        }

    def verify_login(self, *args, **kwargs):
        if args and isinstance(args[0], str):
            username = args[0]
            password = args[1] if len(args) > 1 else ""
        else:
            s = read_settings()
            username = s.get("username", "")
            password = s.get("password", "")

        log_init(f"Verifying login credentials for user '{username}'")

        if not username or not password:
            log_init("Login attempt failed: Empty username or password")
            return {"success": False, "message": "Username and password required"}

        # Batch Auth Routine from settings.bat:
        auth_token = generate_auth_file_xcode(username, password)

        # POST "x=%token%&u=%user%&z=auth" to authp.php
        auth_url = "http://pcmod.ddns.me/commands/authp.php"
        post_data = urllib.parse.urlencode({
            'x': auth_token,
            'u': username,
            'z': 'auth'
        }).encode('utf-8')

        log_init(f"Sending Auth POST Request to {auth_url}: u={username}")

        try:
            req = urllib.request.Request(auth_url, data=post_data, headers={'User-Agent': 'Mozilla/5.0'})
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=2.5, context=ctx) as resp:
                body = resp.read().decode('utf-8', errors='ignore').strip()
                log_init(f"Auth server response: {body}")

                # Check for strict 401.auth password failure
                if "401.auth" in body or "incorrect" in body.lower():
                    log_init(f"Login REJECTED: Password incorrect for {username} ({body})")
                    return {"success": False, "message": "Password was incorrect. Try again."}
                elif "200.auth" in body or "200" in body or "Login Successful" in body or body == "1":
                    USER_INFO["username"] = username
                    USER_INFO["auth_token"] = auth_token
                    USER_INFO["uuid"] = get_uuid_tool_uuid(username)
                    USER_INFO["valid"] = True
                    update_console_title(username)
                    s = read_settings()
                    s["username"] = username
                    write_settings(s)
                    log_init(f"Login SUCCESSFUL for {username}")
                    return {"success": True, "message": "Login successful!"}
                else:
                    log_init(f"Auth response string: {body}")
                    USER_INFO["username"] = username
                    USER_INFO["auth_token"] = auth_token
                    USER_INFO["uuid"] = get_uuid_tool_uuid(username)
                    USER_INFO["valid"] = True
                    update_console_title(username)
                    s = read_settings()
                    s["username"] = username
                    write_settings(s)
                    return {"success": True, "message": "Logged In"}
        except Exception as e:
            log_init(f"Login network exception ({e}) - Falling back to offline user mode")
            USER_INFO["username"] = username
            USER_INFO["auth_token"] = auth_token
            USER_INFO["uuid"] = get_offline_uuid(username)
            USER_INFO["valid"] = True
            update_console_title(username)
            s = read_settings()
            s["username"] = username
            write_settings(s)
            log_init(f"Offline login configured for user {username} (UUID: {USER_INFO['uuid']})")
            return {"success": True, "message": "Offline mode login set"}

    def launch_game(self, *args, **kwargs):
        log_init("launch_game API invoked")
        s = read_settings()
        username = s.get("username", "")
        if not username:
            log_init("Launch game aborted: No username configured")
            if self._window:
                self._window.evaluate_js("alert('Please enter a username and login first!');")
            return False

        pack = get_pack_name()
        mcuuid = get_uuid_tool_uuid(username)
        maxram = s.get("memory", s.get("maxram", "4096"))
        litemode = str(s.get("lite", s.get("litemode", "0"))).strip() in ["1", "true", "True"]
        autoserver = str(s.get("autoserver", "0")).strip() in ["1", "true", "True"]

        log_init(f"Launch Configuration: User={username} | Pack={pack} | Memory={maxram}MB | LiteMode={litemode} | AutoServer={autoserver}")

        mods_dir = os.path.join(DATA_DIR, "packs", pack, "mods")
        if os.path.exists(mods_dir):
            try:
                for f in os.listdir(mods_dir):
                    if litemode:
                        if f.endswith("-client.jar"):
                            os.rename(os.path.join(mods_dir, f), os.path.join(mods_dir, f[:-4] + ".disabled"))
                    else:
                        if f.endswith("-client.disabled"):
                            os.rename(os.path.join(mods_dir, f), os.path.join(mods_dir, f[:-9] + ".jar"))
                log_init("Processed LiteMode client mod file renames")
            except Exception as e:
                log_init(f"Error handling lite mode mod renames: {e}")

        try:
            skin_url = f"http://pcmod.ddns.me/skins/{username}.png"
            skin_dst = os.path.join(DATA_DIR, "cached_skin.png")
            log_init(f"Caching player skin from {skin_url}")
            urllib.request.urlretrieve(skin_url, skin_dst)
        except Exception as se:
            log_init(f"Skin cache retrieve warning: {se}")

        pmc_script = os.path.join(BIN_DIR, "pmc", "portablemc")
        if not os.path.exists(pmc_script) and os.path.exists(os.path.join(BIN_DIR, "pmc", "portablemc.py")):
            pmc_script = os.path.join(BIN_DIR, "pmc", "portablemc.py")

        cmd = [sys.executable, pmc_script, "--main-dir", DATA_DIR, "--work-dir", os.path.join(DATA_DIR, "packs", pack), "start", f"fabric:{pack}", "-u", username, "-i", mcuuid, "-jvm-args", f"-Xmx{maxram}M"]

        if autoserver:
            port = "25565"
            if pack == "2-4-x": port = "25566"
            elif pack == "2-3-x": port = "25567"
            elif pack == "BTW": port = "25568"
            autoserver_args = ["--server", "plattecraft.ddns.net", "--server-port", port]
            cmd.extend(autoserver_args)

        log_init(f"Executing PMC command: {' '.join(cmd)}")

        try:
            launch_log = os.path.join(DATA_DIR, "launch.log")
            with open(launch_log, "a", encoding="utf-8") as lf:
                lf.write(f"\n=== PMC Launch {datetime.now()} ===\n")

            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

            def stream_output(process):
                with open(launch_log, "a", encoding="utf-8") as lf:
                    for line in iter(process.stdout.readline, ''):
                        sys.stdout.write(line)
                        sys.stdout.flush()
                        lf.write(line)
                        lf.flush()
                process.wait()
                log_init(f"Game process exited with code {process.returncode}")

                if process.returncode != 0:
                    try:
                        ftp_str = rot13_5("cg32.3pzbq.qqaf.zr")
                        user_str = rot13_5("ybthc")
                        pass_str = rot13_5("3pzbqybthc123")
                        log_init(f"Uploading crash log to FTP server {ftp_str}")
                        ftp = ftplib.FTP(ftp_str, timeout=5)
                        ftp.login(user_str, pass_str)
                        if os.path.exists(launch_log):
                            with open(launch_log, "rb") as f:
                                ftp.storlines(f"STOR {username}_crash.log", f)
                        ftp.quit()
                        log_init("Crash log uploaded via FTP successfully")
                    except Exception as fe:
                        log_init(f"FTP crash report upload warning: {fe}")

            t = threading.Thread(target=stream_output, args=(proc,))
            t.daemon = True
            t.start()
            return True
        except Exception as e:
            log_init(f"Failed to start game: {e}")
            if self._window:
                self._window.evaluate_js(f"alert('Failed to start game: {e}');")
            return False

    def update_game(self, *args, **kwargs):
        log_init("update_game API invoked")
        return self.run_update(*args, **kwargs)

    def run_update(self, *args, **kwargs):
        log_init("Update game script requested")
        update_bat = os.path.join(CMD_DIR, "update.bat")
        if os.path.exists(update_bat):
            log_init(f"Executing update script: {update_bat}")
            if OS_NAME == "win32":
                subprocess.Popen(["cmd.exe", "/c", update_bat], cwd=BASE_DIR)
            else:
                subprocess.Popen(["bash", update_bat], cwd=BASE_DIR)
            return True
        log_init(f"Update script not found at {update_bat}")
        return False

    def launch_server(self, *args, **kwargs):
        log_init("launch_server API invoked")
        serv_bat = os.path.join(CMD_DIR, "serv.bat")
        if os.path.exists(serv_bat):
            log_init(f"Executing server script: {serv_bat}")
            if OS_NAME == "win32":
                subprocess.Popen(["cmd.exe", "/c", serv_bat], cwd=BASE_DIR)
            else:
                subprocess.Popen(["bash", serv_bat], cwd=BASE_DIR)
            return True
        log_init(f"Server script not found at {serv_bat}")
        return False

def apply_win32_window_icons():
    if OS_NAME == "win32":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            current_pid = kernel32.GetCurrentProcessId()

            IMAGE_ICON = 1
            LR_LOADFROMFILE = 0x00000010
            WM_SETICON = 0x0080
            ICON_SMALL = 0
            ICON_BIG = 1
            GCLP_HICON = -14
            GCLP_HICONSM = -34

            icon_path = os.path.join(DATA_DIR, "icons", "icon.ico")
            if os.path.exists(icon_path):
                hicon_small = user32.LoadImageW(None, icon_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
                hicon_big = user32.LoadImageW(None, icon_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)

                # Callback to apply icon to all windows created by current process
                WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

                def enum_windows_callback(hwnd, lparam):
                    pid = ctypes.c_ulong()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    if pid.value == current_pid:
                        if hicon_small:
                            user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
                        if hicon_big:
                            user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
                        try:
                            if hasattr(user32, 'SetClassLongPtrW'):
                                user32.SetClassLongPtrW(hwnd, GCLP_HICON, hicon_big)
                                user32.SetClassLongPtrW(hwnd, GCLP_HICONSM, hicon_small)
                            else:
                                user32.SetClassLongW(hwnd, GCLP_HICON, hicon_big)
                                user32.SetClassLongW(hwnd, GCLP_HICONSM, hicon_small)
                        except Exception:
                            pass
                    return True

                user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)
                log_init("Enumerate process windows applied icon.ico to all pywebview window handles")
        except Exception as e:
            log_init(f"apply_win32_window_icons error: {e}")

def main():
    api = Api()
    html_path = os.path.join(DATA_DIR, "pages", "launcher.html")
    log_init(f"Launching pywebview GUI with HTML: {html_path}")
    window = webview.create_window(
        "PCMod Client",
        url=f"file://{html_path}",
        js_api=api,
        width=1160,
        height=690,
        resizable=False
    )
    api.set_window(window)

    def on_loaded():
        log_init("pywebview window loaded event fired")
        apply_win32_window_icons()
        if OS_NAME == "win32":
            try:
                import System
                import System.Drawing
                import System.Windows.Forms

                forms = System.Windows.Forms.Application.OpenForms
                for f in forms:
                    icon_path = os.path.join(DATA_DIR, "icons", "icon.ico")
                    if os.path.exists(icon_path):
                        def set_form_icon():
                            try:
                                f.Icon = System.Drawing.Icon(icon_path)
                                f.ShowIcon = True
                                log_init("WinForms form.Icon and ShowIcon set")
                            except Exception as e:
                                log_init(f"WinForms form.Icon error: {e}")

                        f.BeginInvoke(System.Action(set_form_icon))
            except Exception as e:
                log_init(f"WinForms icon setup warning: {e}")

    webview.start(on_loaded, debug=False)

if __name__ == "__main__":
    main()
