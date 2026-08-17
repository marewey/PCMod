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
import socket
import zipfile
import webview
from datetime import datetime

# Ensure data directory exists
OS_NAME = sys.platform
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
BIN_DIR = os.path.join(BASE_DIR, "bin")
OLD_CMD_DIR = os.path.join(BASE_DIR, "_old")
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

        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PCMod.Client.1.0")
        except Exception:
            pass

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
    except Exception:
        pass

def update_console_title(username):
    if OS_NAME == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW(f"PCMod Console - {username}")
        except Exception:
            pass

SETTINGS_FILE = os.path.join(BASE_DIR, "settings.txt")

def get_default_settings():
    return {
        "shortcut": "1",
        "autoserver": "0",
        "log-logins": "1",
        "lite": "0",
        "showconsole": "0",
        "pack": "2-5-x",
        "memory": "4096",
        "username": ""
    }

def read_settings(log_event=False):
    settings_exist = os.path.exists(SETTINGS_FILE)
    settings = get_default_settings()
    if settings_exist:
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip().lower() not in ["password", "debug"]:
                            settings[k.strip()] = v.strip()
            if log_event:
                log_init(f"Read settings.txt successfully: {settings}")
        except Exception:
            pass
    else:
        # Initial creation of settings.txt with defaults
        write_settings(settings)
        if log_event:
            log_init(f"Created initial settings.txt with defaults: {settings}")
        if str(settings.get("shortcut")).strip() in ["1", "true", "True"]:
            toggle_desktop_shortcut(True)
    return settings

def write_settings(settings):
    try:
        lines = []
        for k, v in settings.items():
            if k.lower() in ["password", "debug"]:
                continue
            lines.append(f"{k}={v}\n")
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)
        log_init("Wrote settings.txt successfully")

        if OS_NAME == "win32" and "showconsole" in settings:
            try:
                import ctypes
                hwnd = ctypes.windll.kernel32.GetConsoleWindow()
                if hwnd:
                    show = 1 if str(settings["showconsole"]).strip() in ["1", "true", "True"] else 0
                    ctypes.windll.user32.ShowWindow(hwnd, show)
            except Exception:
                pass
    except Exception:
        pass

init_settings = read_settings(log_event=True)
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

def read_version_info(pack_name):
    launcher_ver = "1.2a"
    pack_ver = "2.5.3a"
    modloader = "forge"
    mcversion = "1.20.1"
    mlversion = "47.4.10"

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
                                if len(parts) >= 3 and parts[2].strip():
                                    modloader = parts[2].strip()
                                if len(parts) >= 4 and parts[3].strip():
                                    mcversion = parts[3].strip()
                                if len(parts) >= 5 and parts[4].strip():
                                    mlversion = parts[4].strip()
            except Exception:
                pass

    return {
        "launcher_ver": launcher_ver,
        "pack_ver": pack_ver,
        "modloader": modloader,
        "mcversion": mcversion,
        "mlversion": mlversion
    }

def read_version_indexes(pack_name):
    info = read_version_info(pack_name)
    return info["launcher_ver"], info["pack_ver"]

def get_portablemc_version_spec(pack_name):
    info = read_version_info(pack_name)
    ml = info["modloader"].lower()
    mc = info["mcversion"]
    mver = info["mlversion"]

    if ml == "vanilla":
        return mc
    elif ml == "fabric":
        return f"fabric:{mc}:{mver}" if mver else f"fabric:{mc}"
    elif ml == "#-btw":
        return mver
    else: # default forge or other loaders
        return f"{ml}:{mc}-{mver}" if mver else f"{ml}:{mc}"

def update_version_index(key, new_ver):
    vfile = os.path.join(DATA_DIR, "indexes", "version")
    lines = []
    found = False
    if os.path.exists(vfile):
        try:
            with open(vfile, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    parts = line.strip().split(";")
                    if len(parts) >= 2 and parts[0].strip() == key:
                        parts[1] = new_ver
                        lines.append(";".join(parts) + "\n")
                        found = True
                    else:
                        lines.append(line)
        except Exception:
            pass
    if not found:
        lines.append(f"{key};{new_ver};PCMod;1.20.1;\n")

    try:
        with open(vfile, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception:
        pass

# Startup Check for PortableMC & Updates
def startup_checks():
    pack = get_pack_name()
    l_ver, p_ver = read_version_indexes(pack)
    log_init(f"Checking for updates... Pack {pack} [{p_ver}] Launcher [{l_ver}]")

    pmc_ver = "4.4.1"
    try:
        pmc_py = os.path.join(BIN_DIR, "pmc", "portablemc", "__init__.py")
        if os.path.exists(pmc_py):
            with open(pmc_py, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if "__version__" in line:
                        match = re.search(r'["\']([^"\']+)["\']', line)
                        if match:
                            pmc_ver = match.group(1)
                            break
    except Exception:
        pass
    log_init(f"Checking for PORTABLEMC... {pmc_ver}")

startup_checks()

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

def read_auth_token(username):
    auth_file = os.path.join(DATA_DIR, "indexes", "auth")
    xcode_exe = os.path.join(BIN_DIR, "xcode.exe")
    if not os.path.exists(auth_file):
        return None
    token = None
    if os.path.exists(xcode_exe) and username:
        try:
            # Decrypt auth file temporarily
            proc = subprocess.Popen([xcode_exe, auth_file], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0x08000000 if OS_NAME=="win32" else 0)
            proc.communicate(input=f"{username}\r\n".encode('utf-8'), timeout=2)
            with open(auth_file, "r", encoding="utf-8", errors="ignore") as f:
                token = f.readline().strip()
            # Re-encrypt auth file
            proc2 = subprocess.Popen([xcode_exe, auth_file], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0x08000000 if OS_NAME=="win32" else 0)
            proc2.communicate(input=f"{username}\r\n".encode('utf-8'), timeout=2)
        except Exception:
            pass
    if not token and os.path.exists(auth_file):
        try:
            with open(auth_file, "r", encoding="utf-8", errors="ignore") as f:
                token = f.readline().strip()
        except Exception:
            pass
    return token

def write_encrypted_auth(username, token_val):
    if not username or not token_val:
        return ""
    auth_file = os.path.join(DATA_DIR, "indexes", "auth")
    os.makedirs(os.path.dirname(auth_file), exist_ok=True)

    raw_hash = token_val
    xcode_exe = os.path.join(BIN_DIR, "xcode.exe")

    if token_val != "404" and os.path.exists(xcode_exe):
        try:
            proc = subprocess.Popen([xcode_exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0x08000000 if OS_NAME=="win32" else 0)
            input_data = f"{username}\r\n{token_val}\r\n".encode('utf-8')
            out, err = proc.communicate(input=input_data, timeout=2)
            lines = [l.strip() for l in out.decode('utf-8', errors='ignore').splitlines() if l.strip()]
            for l in lines:
                if "XOR Tool" in l or "Enter string" in l or "Enter key" in l:
                    continue
                if len(l) == 32:
                    raw_hash = l
                    break
        except Exception:
            pass
    elif token_val == "404":
        raw_hash = "404"

    try:
        with open(auth_file, "w", encoding="utf-8") as f:
            f.write(raw_hash + "\n")
        log_init(f"Saved plain auth token to {auth_file}")
    except Exception as e:
        log_init(f"Error writing auth file: {e}")

    if os.path.exists(xcode_exe):
        try:
            proc = subprocess.Popen([xcode_exe, auth_file], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0x08000000 if OS_NAME=="win32" else 0)
            proc.communicate(input=f"{username}\r\n".encode('utf-8'), timeout=2)
            log_init(f"Encrypted auth file with xcode.exe at {auth_file}")
        except Exception as e:
            log_init(f"xcode auth file encryption error: {e}")

    return raw_hash

def get_xcode_auth(username, password):
    if not username:
        return ""

    if not password:
        raw_token = "404"
    else:
        raw_token = hashlib.md5(password.encode('utf-8')).hexdigest()

    raw_hash = write_encrypted_auth(username, raw_token)
    log_init(f"Auth token generated: {raw_hash}")

    if not raw_hash.startswith("\\"):
        return f"\\{raw_hash}"
    return raw_hash

def get_uuid_tool_uuid(username):
    if not username:
        return ""
    uuid_jar = os.path.join(BIN_DIR, "uuid-tool-1.0.jar")
    if os.path.exists(uuid_jar):
        try:
            proc = subprocess.Popen(["java", "-jar", uuid_jar], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0x08000000 if OS_NAME=="win32" else 0)
            input_data = f"{username}\r\n".encode('utf-8')
            out, err = proc.communicate(input=input_data, timeout=2)
            out_str = out.decode('utf-8', errors='ignore').strip()
            match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', out_str, re.I)
            if match:
                return match.group(0)
        except Exception:
            pass
    return get_offline_uuid(username)

def load_user_info():
    auth_file = os.path.join(DATA_DIR, "indexes", "auth")
    s = read_settings()
    u = s.get("username", "").strip()

    if not os.path.exists(auth_file) or not u:
        USER_INFO["username"] = ""
        USER_INFO["auth_token"] = ""
        USER_INFO["valid"] = False
        if u:
            s["username"] = ""
            write_settings(s)
        return

    token = read_auth_token(u)
    log_init(f"Checking Saved Auth Token for '{u}': {token}")

    if not token:
        USER_INFO["username"] = ""
        USER_INFO["auth_token"] = ""
        USER_INFO["valid"] = False
        s["username"] = ""
        write_settings(s)
        return

    formatted_token = token if token.startswith("\\") else f"\\{token}"

    log_init(f"Authorizing User ({u})...")
    auth_url = "http://pcmod.ddns.me/commands/authp.php"
    post_data = urllib.parse.urlencode({
        'x': formatted_token,
        'u': u,
        'z': 'auth'
    }).encode('utf-8')

    log_init(f"Sending Boot Auth POST Request to {auth_url}: u={u}, x={formatted_token}")

    server_rejected = False
    server_is_404 = False
    try:
        req = urllib.request.Request(auth_url, data=post_data, headers={'User-Agent': 'Mozilla/5.0'})
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=2.5, context=ctx) as resp:
            body = resp.read().decode('utf-8', errors='ignore').strip()
            log_init(f"Boot Auth server response: {body}")

            if "401.auth" in body or "incorrect" in body.lower():
                server_rejected = True
                log_init(f"Boot Auth REJECTED: 401 response for {u}")
            elif "404.auth" in body or "404" in body:
                server_is_404 = True
                log_init(f"Boot Auth SERVER 404: No server auth file found for user {u} ({body})")
            elif "200" in body or body == "":
                log_init(f"Boot Auth SUCCESS (200 OK) for user {u}")
    except Exception as e:
        log_init(f"Boot Auth Network Exception ({e}) - Falling back to offline auth check")

    if server_rejected:
        if os.path.exists(auth_file):
            try:
                os.remove(auth_file)
            except Exception:
                pass
        USER_INFO["username"] = ""
        USER_INFO["auth_token"] = ""
        USER_INFO["valid"] = False
        s["username"] = ""
        write_settings(s)
    else:
        if server_is_404:
            write_encrypted_auth(u, "404")
            formatted_token = "\\404"

        USER_INFO["username"] = u
        USER_INFO["auth_token"] = formatted_token
        USER_INFO["uuid"] = get_uuid_tool_uuid(u)
        USER_INFO["valid"] = True
        update_console_title(u)

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
        except Exception:
            pass
    if not versions:
        versions = [{"name": "2-5-x", "path": os.path.join(DATA_DIR, "packs", "2-5-x")}]
    return versions

# Modlist parsing & HTML generation
def generate_modlist_data(pack_name):
    pak_file = os.path.join(DATA_DIR, "packs", pack_name, f"PCMod-{pack_name}.pak")
    mods = []
    if os.path.exists(pak_file):
        try:
            with open(pak_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line or ";" not in line:
                        continue
                    parts = line.split(";")
                    tag = parts[0].strip()
                    if tag == "D":
                        continue
                    file_name = parts[1].strip() if len(parts) > 1 else ""
                    ver = parts[2].strip() if len(parts) > 2 else ""
                    name = parts[3].strip() if len(parts) > 3 else ""
                    extra = parts[4].strip() if len(parts) > 4 else ""

                    if tag == "U":
                        side = "Universally" if extra in ["#", ""] else "Universally*"
                    elif tag == "C":
                        side = "Client-Side" if extra in ["#", ""] else "Client-Side*"
                    elif tag == "B":
                        side = "Core Mod"
                    elif tag == "S":
                        side = "Server-Side"
                    else:
                        side = "Other"

                    display_name = name if extra in ["#", ""] else f"{name} [{extra}]"
                    mods.append({
                        "tag": tag,
                        "name": display_name,
                        "file": file_name,
                        "version": ver,
                        "side": side
                    })
        except Exception as e:
            log_init(f"Error parsing pak file {pak_file}: {e}")
    return mods

def generate_modlist_html_file(pack_name, mods):
    html_dir = os.path.join(DATA_DIR, "pages")
    os.makedirs(html_dir, exist_ok=True)
    html_path = os.path.join(html_dir, "modlist.html")

    rows = []
    for m in mods:
        tag = m["tag"]
        bg = "#BCF6F6"
        if tag == "U":
            bg = "#A9DDDD" if "*" in m["side"] else "#BCF6F6"
        elif tag == "C":
            bg = "#B7D8AD" if "*" in m["side"] else "#CCF1C1"
        elif tag == "B":
            bg = "#FFAFA6"
        elif tag == "S":
            bg = "#E0E0E0"

        rows.append(f"<tr style='background-color:{bg}; color:#0f172a;'><td>{m['name']}</td><td>{m['side']}</td><td>{m['version']}</td></tr>")

    content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>PCMod Modlist - {pack_name}</title>
<style>
body {{ font-family: sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
th, td {{ padding: 8px 12px; border: 1px solid #334155; text-align: left; }}
th {{ background-color: #1e293b; color: #38bdf8; }}
</style>
</head>
<body>
<h2>Mod List ({len(mods)} mods) - Pack: {pack_name}</h2>
<table>
<thead><tr><th>Mod Name</th><th>Requirement</th><th>Version Added/Updated</th></tr></thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
</body>
</html>"""
    try:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception:
        pass

# login2.php Telemetry Reporting matching exact backend states: in, out, launcher, update, updated, crash
def send_login2_telemetry(state="launcher"):
    try:
        s = read_settings()
        if str(s.get("log-logins", s.get("log_logins", "1"))).strip() not in ["1", "true", "True"]:
            return

        username = s.get("username", "null")
        pack = get_pack_name()
        l_ver, p_ver = read_version_indexes(pack)
        mcuuid = get_uuid_tool_uuid(username) if username else ""
        uuid_val = USER_INFO.get("uuid", f"PC2-0{username[:1] if username else 'X'}")
        memory = str(s.get("memory", s.get("maxram", "4096")))

        mod_dir = os.path.join(DATA_DIR, "packs", pack, "mods")
        modcnt = 0
        if os.path.exists(mod_dir):
            modcnt = sum(1 for f in os.listdir(mod_dir) if f.endswith(".jar") or f.endswith(".zip") or f.endswith(".disabled"))

        try:
            xip = socket.gethostbyname(socket.gethostname())
        except Exception:
            xip = "127.0.0.1"

        versioning = f"{pack}/{p_ver}"

        post_data = urllib.parse.urlencode({
            'user': username,
            'uuid': uuid_val,
            'state': state, # Exact backend state: in, out, launcher, update, updated, crash
            'mcuuid': mcuuid,
            'version': versioning,
            'lversion': l_ver,
            'netinfo': xip,
            'modcount': str(modcnt),
            'memory': memory
        }).encode('utf-8')

        url = "http://pcmod.ddns.me/commands/login2.php"
        log_init(f"Sending telemetry data to server... (state: {state})")

        req = urllib.request.Request(url, data=post_data, headers={'User-Agent': 'Mozilla/5.0'})
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=12.0, context=ctx) as resp:
            resp.read()
    except Exception as e:
        log_init(f"login2.php telemetry exception: {e}")

def toggle_desktop_shortcut(enable):
    if OS_NAME == "win32":
        try:
            target = sys.executable
            script_file = os.path.abspath(__file__)
            icon_path = os.path.join(DATA_DIR, "icons", "icon.ico")
            vbs_file = os.path.join(DATA_DIR, "create_shortcut.vbs")

            if enable:
                vbs_script = (
                    'Set ws = WScript.CreateObject("WScript.Shell")\n'
                    'desktopPath = ws.SpecialFolders("Desktop")\n'
                    'shortcutPath = desktopPath & "\\PCMod Client.lnk"\n'
                    'Set sc = ws.CreateShortcut(shortcutPath)\n'
                    f'sc.TargetPath = "{target}"\n'
                    f'sc.Arguments = "{script_file}"\n'
                    f'sc.WorkingDirectory = "{BASE_DIR}"\n'
                    f'sc.IconLocation = "{icon_path}"\n'
                    'sc.Save\n'
                )
                with open(vbs_file, "w", encoding="utf-8") as f:
                    f.write(vbs_script)
                subprocess.run(["cscript", "//Nologo", vbs_file], timeout=5)
                if os.path.exists(vbs_file):
                    os.remove(vbs_file)
                log_init("Created desktop shortcut: PCMod Client.lnk via WScript SpecialFolders")
            else:
                vbs_script = (
                    'Set ws = WScript.CreateObject("WScript.Shell")\n'
                    'desktopPath = ws.SpecialFolders("Desktop")\n'
                    'shortcutPath = desktopPath & "\\PCMod Client.lnk"\n'
                    'Set fso = CreateObject("Scripting.FileSystemObject")\n'
                    'If fso.FileExists(shortcutPath) Then fso.DeleteFile(shortcutPath)\n'
                )
                with open(vbs_file, "w", encoding="utf-8") as f:
                    f.write(vbs_script)
                subprocess.run(["cscript", "//Nologo", vbs_file], timeout=5)
                if os.path.exists(vbs_file):
                    os.remove(vbs_file)
                log_init("Removed desktop shortcut: PCMod Client.lnk via WScript SpecialFolders")
        except Exception as e:
            log_init(f"Desktop shortcut error: {e}")

UPDATE_IN_PROGRESS = False
UPDATE_CANCEL_REQUESTED = False

# Server Update Check & Download Engine
def check_updates_server():
    pack = get_pack_name()
    l_ver, p_ver = read_version_indexes(pack)

    url = "http://pcmod.ddns.me/version"
    tmp_file = os.path.join(DATA_DIR, "indexes", "version.tmp")

    remote_versions = {}

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=3.0, context=ctx) as resp:
            raw_text = resp.read().decode('utf-8', errors='ignore')
            if raw_text:
                lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
                clean_content = "\n".join(lines) + "\n"
                with open(tmp_file, "w", encoding="utf-8") as f:
                    f.write(clean_content)
    except Exception as e:
        log_init(f"Update check network warning: {e}")

    if os.path.exists(tmp_file):
        try:
            with open(tmp_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    parts = line.strip().split(";")
                    if len(parts) >= 2:
                        key = parts[0].strip()
                        ver = parts[1].strip()
                        remote_versions[key] = ver
        except Exception:
            pass

    launcher_update = ""
    if remote_versions.get("Launcher") and remote_versions.get("Launcher") != l_ver:
        launcher_update = remote_versions.get("Launcher")

    installed_versions = get_versions_list()
    pack_updates = []
    primary_pack_update = ""

    for item in installed_versions:
        p_name = item["name"]
        _, current_p_ver = read_version_indexes(p_name)
        remote_p_ver = remote_versions.get(p_name, "")
        if remote_p_ver and remote_p_ver != current_p_ver:
            pack_updates.append({
                "pack": p_name,
                "current_version": current_p_ver,
                "new_version": remote_p_ver
            })
            if p_name == pack:
                primary_pack_update = remote_p_ver

    return {
        "current_launcher": l_ver,
        "current_pack": p_ver,
        "pack": pack,
        "launcher_update": launcher_update,
        "pack_update": primary_pack_update,
        "pack_updates": pack_updates,
        "update_available": bool(launcher_update or len(pack_updates) > 0)
    }

def get_remote_file_size(url, size_url=None):
    if size_url:
        try:
            req = urllib.request.Request(size_url, headers={'User-Agent': 'Mozilla/5.0'})
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=2.5, context=ctx) as resp:
                raw = resp.read().decode('utf-8', errors='ignore').strip()
                if raw.isdigit():
                    return int(raw)
        except Exception:
            pass

    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=3.0, context=ctx) as resp:
            cl = resp.headers.get('Content-Length')
            if cl and cl.isdigit():
                return int(cl)
    except Exception:
        pass

    return 0

def download_with_progress_and_size(url, dst_path, size_url=None, progress_callback=None, title="Downloading..."):
    global UPDATE_CANCEL_REQUESTED
    total_bytes = get_remote_file_size(url, size_url)

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    with urllib.request.urlopen(req, timeout=10.0, context=ctx) as resp:
        if not total_bytes:
            cl = resp.headers.get('Content-Length')
            if cl and cl.isdigit():
                total_bytes = int(cl)

        downloaded = 0
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        with open(dst_path, "wb") as f:
            chunk_size = 64 * 1024
            while True:
                if UPDATE_CANCEL_REQUESTED:
                    raise Exception("Update cancelled by user.")
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)

                if progress_callback:
                    percent = int((downloaded / total_bytes) * 100) if total_bytes > 0 else 0
                    dl_mb = round(downloaded / (1024 * 1024), 2)
                    tot_mb = round(total_bytes / (1024 * 1024), 2) if total_bytes > 0 else 0
                    msg = f"Downloaded {dl_mb} MB / {tot_mb} MB ({percent}%)" if total_bytes > 0 else f"Downloaded {dl_mb} MB"
                    progress_callback({
                        "status": "downloading",
                        "title": title,
                        "message": msg,
                        "percent": percent,
                        "downloaded_bytes": downloaded,
                        "total_bytes": total_bytes,
                        "downloaded_str": f"{dl_mb} MB",
                        "total_str": f"{tot_mb} MB" if total_bytes > 0 else "Unknown",
                        "update_in_progress": True
                    })
    return True

def extract_zip_with_progress(zip_path, extract_dir, progress_callback=None, title="Extracting..."):
    global UPDATE_CANCEL_REQUESTED
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        members = zip_ref.infolist()
        total_files = len(members)
        for i, member in enumerate(members, 1):
            if UPDATE_CANCEL_REQUESTED:
                raise Exception("Update cancelled by user.")
            zip_ref.extract(member, extract_dir)
            if progress_callback and total_files > 0:
                percent = int((i / total_files) * 100)
                progress_callback({
                    "status": "extracting",
                    "title": title,
                    "message": f"Extracting {member.filename} ({i}/{total_files})",
                    "percent": percent,
                    "update_in_progress": True
                })

def restart_launcher():
    log_init("Restarting PCMod Launcher...")
    python_exe = sys.executable
    script_file = os.path.abspath(__file__)
    subprocess.Popen([python_exe, script_file] + sys.argv[1:])
    os._exit(0)

class Api:
    def __init__(self):
        self._window = None

    def set_window(self, window):
        self._window = window

    def init_launcher(self, *args, **kwargs):
        s = read_settings()
        pack = get_pack_name()
        modcount = self.get_mod_count()
        launcher_ver, pack_ver = read_version_indexes(pack)

        # Check line 2 of version file to determine main default pack
        main_pack = pack
        version_file = os.path.join(DATA_DIR, "indexes", "version")
        if os.path.exists(version_file):
            try:
                with open(version_file, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [l.strip() for l in f if l.strip()]
                    if len(lines) >= 2:
                        parts = lines[1].split(";")
                        if parts[0].strip():
                            main_pack = parts[0].strip()
            except Exception:
                pass

        main_pack_installed = os.path.exists(os.path.join(DATA_DIR, "packs", main_pack))

        return {
            "user": s.get("username", ""),
            "settings": {
                "shortcut": "1" if str(s.get("shortcut")).strip() in ["1", "true", "True"] else "0",
                "autoserver": "1" if str(s.get("autoserver")).strip() in ["1", "true", "True"] else "0",
                "log_logins": "1" if str(s.get("log-logins", s.get("log_logins", "1"))).strip() in ["1", "true", "True"] else "0",
                "log-logins": "1" if str(s.get("log-logins", s.get("log_logins", "1"))).strip() in ["1", "true", "True"] else "0",
                "lite": "1" if str(s.get("lite", s.get("litemode", "0"))).strip() in ["1", "true", "True"] else "0",
                "showconsole": "1" if str(s.get("showconsole")).strip() in ["1", "true", "True"] else "0",
                "memory": str(s.get("memory", s.get("maxram", "4096"))),
                "pack": pack
            },
            "modcount": str(modcount),
            "launcher_version": launcher_ver,
            "pack_version": pack_ver,
            "versions_list": get_versions_list(),
            "main_pack": main_pack,
            "main_pack_installed": main_pack_installed,
            "online_players": "Loading...",
            "news_url": "news.html"
        }

    def get_settings(self, *args, **kwargs):
        return read_settings()

    def save_settings(self, *args, **kwargs):
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
        return self.save_settings(*args, **kwargs)

    def set_setting(self, *args, **kwargs):
        if len(args) >= 2:
            k, v = args[0], args[1]
            s = read_settings()
            s[str(k)] = str(v)
            write_settings(s)
            if str(k) == "shortcut":
                toggle_desktop_shortcut(str(v) in ["1", "true", "True"])
        return True

    def set_lite_mode(self, *args, **kwargs):
        val = args[0] if args else "0"
        s = read_settings()
        s["lite"] = str(val)
        write_settings(s)
        return True

    def set_memory(self, *args, **kwargs):
        val = args[0] if args else "4096"
        s = read_settings()
        s["memory"] = str(val)
        write_settings(s)
        return True

    def set_version_select(self, *args, **kwargs):
        val = args[0] if args else ""
        if " " in str(val):
            val = str(val).split(" ", 1)[1]
        s = read_settings()
        s["pack"] = str(val)
        write_settings(s)
        return True

    def get_mod_count(self, *args, **kwargs):
        pack = get_pack_name()
        mods = generate_modlist_data(pack)
        if mods:
            return len(mods)
        mods_dir = os.path.join(DATA_DIR, "packs", pack, "mods")
        if os.path.exists(mods_dir):
            try:
                count = sum(1 for f in os.listdir(mods_dir) if f.endswith(".jar") or f.endswith(".zip") or f.endswith(".disabled"))
                return count
            except Exception:
                pass
        return 0

    def get_available_packs_manifest(self, *args, **kwargs):
        packs = []
        vfile = os.path.join(DATA_DIR, "indexes", "version")
        if os.path.exists(vfile):
            try:
                with open(vfile, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        parts = line.strip().split(";")
                        if len(parts) >= 2:
                            k = parts[0].strip()
                            if k.lower() == "launcher":
                                continue
                            ver = parts[1].strip()
                            loader = parts[2].strip() if len(parts) >= 3 else "forge"
                            installed = os.path.exists(os.path.join(DATA_DIR, "packs", k))
                            packs.append({
                                "name": k,
                                "version": ver,
                                "modloader": loader,
                                "installed": installed
                            })
            except Exception:
                pass

        if not packs:
            packs = [{
                "name": "2-5-x",
                "version": "2.5.3a",
                "modloader": "forge",
                "installed": os.path.exists(os.path.join(DATA_DIR, "packs", "2-5-x"))
            }]

        return {"packs": packs}

    def get_modlist(self, *args, **kwargs):
        pack = get_pack_name()
        mods = generate_modlist_data(pack)
        generate_modlist_html_file(pack, mods)
        return {"pack": pack, "count": len(mods), "mods": mods}

    def open_modlist(self, *args, **kwargs):
        pack = get_pack_name()
        mods = generate_modlist_data(pack)
        generate_modlist_html_file(pack, mods)
        return {"pack": pack, "count": len(mods), "mods": mods}

    def open_link(self, *args, **kwargs):
        url = args[0] if args else "http://pcmod.ddns.me"
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
        return self.open_link(url)

    def get_news_url(self, *args, **kwargs):
        remote_url = "https://pcmod.ddns.me/updates/news.html"
        local_news_path = os.path.join(DATA_DIR, "pages", "news.html")
        os.makedirs(os.path.join(DATA_DIR, "pages"), exist_ok=True)
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
                    except Exception:
                        pass
                    return remote_url
        except Exception:
            pass

        if os.path.exists(local_news_path):
            return "news.html"
        return "news.html"

    def get_players_online(self, *args, **kwargs):
        pack = get_pack_name()
        url = f"http://pcmod.ddns.me/players/list-{pack}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=1.5, context=ctx) as response:
                text = response.read().decode('utf-8', errors='ignore').strip()
                players = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("<")]
                if players:
                    html_lines = "<br>".join([f"• {p}" for p in players])
                    return {"status": f"{len(players)} Online", "players": players, "players_html": html_lines}
                return {"status": "No Players Online", "players": [], "players_html": "No players online"}
        except Exception:
            return {"status": "Server Offline", "players": [], "players_html": "Server Offline"}

    def refresh_players(self, *args, **kwargs):
        res = self.get_players_online()
        return res.get("players_html", res.get("status", "No players online"))

    def login(self, *args, **kwargs):
        username = args[0] if len(args) > 0 else ""
        password = args[1] if len(args) > 1 else ""
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
        log_init(f"Checking User Length: {len(username)}")
        log_init(f"Authorizing User ({username})...")

        if not username:
            return {"success": False, "message": "Username required"}

        # Calculate auth token with leading backslash (\hash)
        auth_token = get_xcode_auth(username, password)

        # POST "x=%token%&u=%user%&z=auth" to authp.php
        auth_url = "http://pcmod.ddns.me/commands/authp.php"
        post_data = urllib.parse.urlencode({
            'x': auth_token,
            'u': username,
            'z': 'auth'
        }).encode('utf-8')

        log_init(f"Sending Auth POST Request to {auth_url}: u={username}")

        server_auth_success = False
        try:
            req = urllib.request.Request(auth_url, data=post_data, headers={'User-Agent': 'Mozilla/5.0'})
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=2.5, context=ctx) as resp:
                body = resp.read().decode('utf-8', errors='ignore').strip()
                log_init(f"Auth server response: {body}")

                if "401.auth" in body or "incorrect" in body.lower():
                    log_init(f"Login REJECTED: Password incorrect for {username} ({body})")
                    auth_file = os.path.join(DATA_DIR, "indexes", "auth")
                    if os.path.exists(auth_file):
                        try:
                            os.remove(auth_file)
                        except Exception:
                            pass
                    USER_INFO["username"] = ""
                    USER_INFO["auth_token"] = ""
                    USER_INFO["valid"] = False
                    s = read_settings()
                    s["username"] = ""
                    write_settings(s)
                    return {"success": False, "message": "Password was incorrect. Try again."}
                else:
                    if "404.auth" in body or "404" in body:
                        log_init(f"Login 404 response ({body}): No auth file on server for user {username}. Saving 404 placeholder.")
                        write_encrypted_auth(username, "404")
                        auth_token = "\\404"

                    server_auth_success = True
                    USER_INFO["username"] = username
                    USER_INFO["auth_token"] = auth_token
                    USER_INFO["uuid"] = get_uuid_tool_uuid(username)
                    USER_INFO["valid"] = True
                    update_console_title(username)
                    s = read_settings()
                    s["username"] = username
                    write_settings(s)
                    threading.Thread(target=send_login2_telemetry, args=("in",), daemon=True).start()
                    return {"success": True, "message": "Logged In"}
        except Exception as e:
            log_init(f"Auth Network Exception ({e})")

        # Offline Mode logic: Allow offline login ONLY if auth file exists!
        auth_file = os.path.join(DATA_DIR, "indexes", "auth")
        if os.path.exists(auth_file) and not server_auth_success:
            USER_INFO["username"] = username
            USER_INFO["auth_token"] = auth_token
            USER_INFO["uuid"] = get_offline_uuid(username)
            USER_INFO["valid"] = True
            update_console_title(username)
            s = read_settings()
            s["username"] = username
            write_settings(s)
            log_init(f"Offline login allowed for previously authenticated user {username}")
            return {"success": True, "message": "Offline mode login set"}

        log_init(f"Login REJECTED: Unable to authenticate user {username}")
        s = read_settings()
        s["username"] = ""
        write_settings(s)
        USER_INFO["username"] = ""
        USER_INFO["valid"] = False
        return {"success": False, "message": "Login failed: Server offline and no saved authentication session."}

    def launch_game(self, *args, **kwargs):
        s = read_settings()
        username = s.get("username", "").strip()
        if not username:
            log_init("Launch prevented: No username logged in")
            if self._window:
                self._window.evaluate_js("alert('Please enter a username and login first!');")
            return False

        pack = get_pack_name()
        mcuuid = get_uuid_tool_uuid(username)
        maxram = s.get("memory", s.get("maxram", "4096"))
        litemode = str(s.get("lite", s.get("litemode", "0"))).strip() in ["1", "true", "True"]
        autoserver = str(s.get("autoserver", "0")).strip() in ["1", "true", "True"]

        log_init(f"Launching Game: User={username} | Pack={pack} | Memory={maxram}MB")

        # Telemetry logging with 'launcher' state
        threading.Thread(target=send_login2_telemetry, args=("launcher",), daemon=True).start()

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
            except Exception:
                pass

        try:
            skin_url = f"http://pcmod.ddns.me/skins/{username}.png"
            skin_dst = os.path.join(DATA_DIR, "cached_skin.png")
            urllib.request.urlretrieve(skin_url, skin_dst)
        except Exception:
            pass

        jvm_args_str = f"-Xmx{maxram}M -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M"

        # Load extra JVM args from data/indexes/jvm_args if present
        extra_jvm_args_file = os.path.join(DATA_DIR, "indexes", "jvm_args")
        if os.path.exists(extra_jvm_args_file):
            try:
                with open(extra_jvm_args_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        jvm_args_str += " " + content
            except Exception:
                pass

        # Resolve portablemc version target spec from version indexes (matching launch.bat %m-version%)
        m_version = get_portablemc_version_spec(pack)

        # Execution using PYTHONPATH=bin/pmc and python -m portablemc to prevent http.py import shadowing!
        cmd = [sys.executable, "-m", "portablemc", "--main-dir", DATA_DIR, "--work-dir", os.path.join(DATA_DIR, "packs", pack), "start", m_version, "-u", username, "-i", mcuuid, f"--jvm-args={jvm_args_str}"]

        if autoserver:
            port = "25565"
            if pack == "2-4-x": port = "25566"
            elif pack == "2-3-x": port = "25567"
            elif pack == "BTW": port = "25568"
            autoserver_args = ["--server", "plattecraft.ddns.net", "--server-port", port]
            cmd.extend(autoserver_args)

        # Check if modloader/assets/version structure is missing
        needs_install = False
        vinfo = read_version_info(pack)
        modloader = vinfo.get("modloader", "").lower()
        mcversion = vinfo.get("mcversion", "")
        mlversion = vinfo.get("mlversion", "")

        pack_dir = os.path.join(DATA_DIR, "packs", pack)
        if not os.path.exists(pack_dir):
            needs_install = True
        elif not os.path.exists(os.path.join(pack_dir, "assets", "indexes")):
            needs_install = True
        elif modloader != "vanilla" and not os.path.exists(os.path.join(pack_dir, "versions", f"{modloader}-{mcversion}-{mlversion}")):
            needs_install = True

        proc_env = os.environ.copy()
        pmc_dir = os.path.join(BIN_DIR, "pmc")
        if "PYTHONPATH" in proc_env:
            proc_env["PYTHONPATH"] = pmc_dir + os.pathsep + proc_env["PYTHONPATH"]
        else:
            proc_env["PYTHONPATH"] = pmc_dir

        def launch_runner():
            try:
                if needs_install:
                    log_init(f"Modloader/assets missing for pack '{pack}'. Downloading missing resources...")
                    if self._window:
                        self._window.evaluate_js("onGameLaunchState('downloading');")
                    dry_cmd = [sys.executable, "-m", "portablemc", "--main-dir", DATA_DIR, "--work-dir", pack_dir, "start", "--dry", m_version]
                    try:
                        p_dry = subprocess.Popen(dry_cmd, env=proc_env, cwd=BASE_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                        for line in iter(p_dry.stdout.readline, ''):
                            sys.stdout.write(line)
                            sys.stdout.flush()
                        p_dry.wait()
                    except Exception as e:
                        log_init(f"Dry run resource setup error: {e}")

                if self._window:
                    self._window.evaluate_js("onGameLaunchState('running');")

                log_init(f"Executing PMC command: {' '.join(cmd)}")
                launch_log = os.path.join(DATA_DIR, "launch.log")
                with open(launch_log, "a", encoding="utf-8") as lf:
                    lf.write(f"\n=== PMC Launch {datetime.now()} ===\n")

                proc = subprocess.Popen(cmd, env=proc_env, cwd=BASE_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

                with open(launch_log, "a", encoding="utf-8") as lf:
                    for line in iter(proc.stdout.readline, ''):
                        sys.stdout.write(line)
                        sys.stdout.flush()
                        lf.write(line)
                        lf.flush()
                proc.wait()
                log_init(f"Game process exited with code {proc.returncode}")

                if proc.returncode != 0:
                    threading.Thread(target=send_login2_telemetry, args=("crash",), daemon=True).start()
                    try:
                        ftp_str = rot13_5("cg32.3pzbq.qqaf.zr")
                        user_str = rot13_5("ybthc")
                        pass_str = rot13_5("3pzbqybthc123")
                        ftp = ftplib.FTP(ftp_str, timeout=5)
                        ftp.login(user_str, pass_str)
                        if os.path.exists(launch_log):
                            with open(launch_log, "rb") as f:
                                ftp.storlines(f"STOR {username}_crash.log", f)
                        ftp.quit()
                        log_init("Crash log uploaded via FTP successfully")
                    except Exception:
                        pass
            finally:
                if self._window:
                    self._window.evaluate_js("onGameLaunchState('idle');")

        try:
            t = threading.Thread(target=launch_runner)
            t.daemon = True
            t.start()
            return True
        except Exception as e:
            log_init(f"Failed to start game: {e}")
            if self._window:
                self._window.evaluate_js(f"alert('Failed to start game: {e}');")
            return False

    def check_updates(self, *args, **kwargs):
        return check_updates_server()

    def cancel_update_action(self, *args, **kwargs):
        global UPDATE_CANCEL_REQUESTED
        log_init("Update cancellation requested by user")
        UPDATE_CANCEL_REQUESTED = True
        return True

    def run_update_action(self, action, target_version=None, *args, **kwargs):
        global UPDATE_IN_PROGRESS, UPDATE_CANCEL_REQUESTED
        UPDATE_IN_PROGRESS = True
        UPDATE_CANCEL_REQUESTED = False

        def notify_progress(info):
            if self._window:
                safe_json = json.dumps(info)
                self._window.evaluate_js(f"if(window.onUpdateProgress) window.onUpdateProgress({safe_json});")

        def worker():
            global UPDATE_IN_PROGRESS, UPDATE_CANCEL_REQUESTED
            pack = get_pack_name()
            notify_progress({"status": "starting", "title": "Preparing Update...", "percent": 0, "update_in_progress": True})
            threading.Thread(target=send_login2_telemetry, args=("update",), daemon=True).start()

            try:
                if action in ["auto", "autoupdate"]:
                    up_info = check_updates_server()
                    l_up = up_info.get("launcher_update")
                    p_updates = up_info.get("pack_updates", [])

                    if l_up:
                        notify_progress({"status": "downloading", "title": f"Downloading Launcher Update v{l_up}...", "percent": 10, "update_in_progress": True})
                        zip_path = os.path.join(DATA_DIR, "update", f"launcher_{l_up}.zip")
                        url = f"http://pcmod.ddns.me/updates/launcher/launcher_{l_up}.zip"
                        size_url = f"http://pcmod.ddns.me/updates/launcher/sizes/launcher_{l_up}.size"
                        try:
                            download_with_progress_and_size(url, zip_path, size_url, notify_progress, f"Downloading Launcher Update v{l_up}")
                            notify_progress({"status": "extracting", "title": "Extracting Launcher Update...", "percent": 70, "update_in_progress": True})
                            ext_dir = os.path.join(DATA_DIR, "update", f"launcher_{l_up}")
                            extract_zip_with_progress(zip_path, ext_dir, notify_progress, "Extracting Launcher Update")
                            notify_progress({"status": "installing", "title": "Installing Launcher Update...", "percent": 90, "update_in_progress": True})
                            for root, dirs, files in os.walk(ext_dir):
                                rel_path = os.path.relpath(root, ext_dir)
                                dst_dir = BASE_DIR if rel_path == "." else os.path.join(BASE_DIR, rel_path)
                                os.makedirs(dst_dir, exist_ok=True)
                                for file in files:
                                    src_file = os.path.join(root, file)
                                    dst_file = os.path.join(dst_dir, file)
                                    try:
                                        with open(src_file, "rb") as sf, open(dst_file, "wb") as df:
                                            df.write(sf.read())
                                    except Exception:
                                        pass
                            update_version_index("Launcher", l_up)
                            notify_progress({"status": "complete", "title": "Launcher Update Complete!", "message": "Restarting PCMod...", "percent": 100, "update_in_progress": False})
                            UPDATE_IN_PROGRESS = False
                            threading.Thread(target=send_login2_telemetry, args=("updated",), daemon=True).start()
                            time.sleep(1.5)
                            restart_launcher()
                            return
                        except Exception as e:
                            if UPDATE_CANCEL_REQUESTED:
                                notify_progress({"status": "cancelled", "title": "Update Cancelled", "message": "Launcher update cancelled.", "percent": 0, "update_in_progress": False})
                            else:
                                notify_progress({"status": "error", "title": "Launcher Update Error", "message": str(e), "percent": 0, "update_in_progress": False})
                            return

                    if p_updates:
                        total_packs = len(p_updates)
                        for idx, p_item in enumerate(p_updates, 1):
                            p_name = p_item["pack"]
                            p_ver = p_item["new_version"]
                            notify_progress({"status": "downloading", "title": f"Updating Pack {p_name} ({idx}/{total_packs}) v{p_ver}...", "percent": 10, "update_in_progress": True})
                            zip_path = os.path.join(DATA_DIR, "update", f"pack_{p_ver}.zip")
                            url = f"http://pcmod.ddns.me/updates/pack/{p_name}/pack_{p_ver}.zip"
                            size_url = f"http://pcmod.ddns.me/updates/pack/{p_name}/sizes/pack_{p_ver}.size"
                            try:
                                download_with_progress_and_size(url, zip_path, size_url, notify_progress, f"Downloading Pack {p_name} v{p_ver}")
                                ext_dir = os.path.join(DATA_DIR, "update", f"pack_{p_ver}")
                                extract_zip_with_progress(zip_path, ext_dir, notify_progress, f"Extracting Pack {p_name} v{p_ver}")
                                dst_pack_dir = os.path.join(DATA_DIR, "packs", p_name)
                                os.makedirs(dst_pack_dir, exist_ok=True)
                                for root, dirs, files in os.walk(ext_dir):
                                    rel_path = os.path.relpath(root, ext_dir)
                                    dst_dir = dst_pack_dir if rel_path == "." else os.path.join(dst_pack_dir, rel_path)
                                    os.makedirs(dst_dir, exist_ok=True)
                                    for file in files:
                                        src_file = os.path.join(root, file)
                                        dst_file = os.path.join(dst_dir, file)
                                        try:
                                            with open(src_file, "rb") as sf, open(dst_file, "wb") as df:
                                                df.write(sf.read())
                                        except Exception:
                                            pass
                                update_version_index(p_name, p_ver)
                            except Exception as e:
                                if UPDATE_CANCEL_REQUESTED:
                                    notify_progress({"status": "cancelled", "title": "Update Cancelled", "message": "Pack update cancelled.", "percent": 0, "update_in_progress": False})
                                    return
                                else:
                                    notify_progress({"status": "error", "title": "Pack Update Error", "message": str(e), "percent": 0, "update_in_progress": False})
                                    return

                        notify_progress({"status": "complete", "title": "Pack Updates Complete!", "message": f"Updated {total_packs} packs.", "percent": 100, "update_in_progress": False})
                        threading.Thread(target=send_login2_telemetry, args=("updated",), daemon=True).start()
                        return

                    notify_progress({"status": "complete", "title": "No Updates Needed", "message": "Your Launcher and Packs are up to date!", "percent": 100, "update_in_progress": False})

                elif action == "refresh_mods":
                    notify_progress({"status": "downloading", "title": "Refreshing Mods...", "message": "Checking mod integrity...", "percent": 10, "update_in_progress": True})
                    pak_file = os.path.join(DATA_DIR, "packs", pack, f"PCMod-{pack}.pak")
                    mods_dir = os.path.join(DATA_DIR, "packs", pack, "mods")
                    os.makedirs(mods_dir, exist_ok=True)

                    mods_to_download = []
                    if os.path.exists(pak_file):
                        with open(pak_file, "r", encoding="utf-8", errors="ignore") as f:
                            for line in f:
                                parts = line.strip().split(";")
                                if len(parts) >= 2 and parts[0].strip() in ["U", "C", "B"]:
                                    mod_file = parts[1].strip()
                                    mod_name = parts[3].strip() if len(parts) > 3 else mod_file
                                    mods_to_download.append((mod_file, mod_name))

                    total_mods = len(mods_to_download)
                    for idx, (mfile, mname) in enumerate(mods_to_download, 1):
                        if UPDATE_CANCEL_REQUESTED:
                            notify_progress({"status": "cancelled", "title": "Update Cancelled", "message": "Mod refresh cancelled.", "percent": 0, "update_in_progress": False})
                            return
                        mod_path = os.path.join(mods_dir, mfile)
                        url = f"http://pcmod.ddns.me/mods/{pack}/{mfile}"
                        pct = int((idx / total_mods) * 100) if total_mods > 0 else 100
                        notify_progress({
                            "status": "downloading",
                            "title": "Refreshing Mods...",
                            "message": f"Downloading {mname} ({idx}/{total_mods})",
                            "percent": pct,
                            "update_in_progress": True
                        })
                        try:
                            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                            ctx = ssl.create_default_context()
                            ctx.check_hostname = False
                            ctx.verify_mode = ssl.CERT_NONE
                            with urllib.request.urlopen(req, timeout=5.0, context=ctx) as resp:
                                with open(mod_path, "wb") as mf:
                                    mf.write(resp.read())
                        except Exception:
                            pass

                    notify_progress({"status": "complete", "title": "Refresh Mods Complete!", "message": f"Verified {total_mods} mods.", "percent": 100, "update_in_progress": False})

                elif action == "launcher_update":
                    ver = target_version or "latest"
                    notify_progress({"status": "downloading", "title": f"Updating Launcher (v{ver})...", "percent": 10, "update_in_progress": True})
                    zip_path = os.path.join(DATA_DIR, "update", f"launcher_{ver}.zip")
                    urls = [
                        f"http://pcmod.ddns.me/download/launcher/launcher-{ver}.zip",
                        f"http://pcmod.ddns.me/updates/launcher/launcher_{ver}.zip"
                    ]
                    size_urls = [
                        f"http://pcmod.ddns.me/download/launcher/sizes/launcher-{ver}.size",
                        f"http://pcmod.ddns.me/updates/launcher/sizes/launcher_{ver}.size"
                    ]

                    downloaded = False
                    for u, su in zip(urls, size_urls):
                        try:
                            download_with_progress_and_size(u, zip_path, su, notify_progress, f"Downloading Launcher v{ver}")
                            downloaded = True
                            break
                        except Exception as e:
                            if UPDATE_CANCEL_REQUESTED:
                                notify_progress({"status": "cancelled", "title": "Update Cancelled", "message": "Launcher update cancelled.", "percent": 0, "update_in_progress": False})
                                return
                            log_init(f"Launcher update download failed for {u}: {e}")

                    if downloaded and os.path.exists(zip_path):
                        try:
                            ext_dir = os.path.join(DATA_DIR, "update", f"launcher_{ver}")
                            extract_zip_with_progress(zip_path, ext_dir, notify_progress, f"Extracting Launcher v{ver}")
                            notify_progress({"status": "installing", "title": "Installing Launcher Update...", "percent": 90, "update_in_progress": True})
                            for root, dirs, files in os.walk(ext_dir):
                                rel_path = os.path.relpath(root, ext_dir)
                                dst_dir = BASE_DIR if rel_path == "." else os.path.join(BASE_DIR, rel_path)
                                os.makedirs(dst_dir, exist_ok=True)
                                for file in files:
                                    src_file = os.path.join(root, file)
                                    dst_file = os.path.join(dst_dir, file)
                                    try:
                                        with open(src_file, "rb") as sf, open(dst_file, "wb") as df:
                                            df.write(sf.read())
                                    except Exception:
                                        pass
                            update_version_index("Launcher", ver)
                            notify_progress({"status": "complete", "title": "Launcher Update Complete!", "message": "Restarting PCMod...", "percent": 100, "update_in_progress": False})
                            threading.Thread(target=send_login2_telemetry, args=("updated",), daemon=True).start()
                            time.sleep(1.5)
                            restart_launcher()
                            return
                        except Exception as e:
                            if UPDATE_CANCEL_REQUESTED:
                                notify_progress({"status": "cancelled", "title": "Update Cancelled", "message": "Launcher update cancelled.", "percent": 0, "update_in_progress": False})
                            else:
                                notify_progress({"status": "error", "title": "Launcher Update Error", "message": str(e), "percent": 0, "update_in_progress": False})
                    else:
                        if UPDATE_CANCEL_REQUESTED:
                            notify_progress({"status": "cancelled", "title": "Update Cancelled", "message": "Launcher update cancelled.", "percent": 0, "update_in_progress": False})
                        else:
                            notify_progress({"status": "error", "title": "Launcher Update Error", "message": "Failed to download launcher update zip.", "percent": 0, "update_in_progress": False})

                elif action == "pack_update":
                    ver = target_version or "latest"
                    notify_progress({"status": "downloading", "title": f"Updating Pack {pack} (v{ver})...", "percent": 10, "update_in_progress": True})
                    zip_path = os.path.join(DATA_DIR, "update", f"pack_{ver}.zip")
                    urls = [
                        f"http://pcmod.ddns.me/download/pack/{pack}/pack_{ver}.zip",
                        f"http://pcmod.ddns.me/updates/pack/{pack}/pack_{ver}.zip"
                    ]
                    size_urls = [
                        f"http://pcmod.ddns.me/download/pack/{pack}/sizes/pack_{ver}.size",
                        f"http://pcmod.ddns.me/updates/pack/{pack}/sizes/pack_{ver}.size"
                    ]

                    downloaded = False
                    for u, su in zip(urls, size_urls):
                        try:
                            download_with_progress_and_size(u, zip_path, su, notify_progress, f"Downloading Pack {pack} v{ver}")
                            downloaded = True
                            break
                        except Exception as e:
                            if UPDATE_CANCEL_REQUESTED:
                                notify_progress({"status": "cancelled", "title": "Update Cancelled", "message": "Pack update cancelled.", "percent": 0, "update_in_progress": False})
                                return
                            log_init(f"Pack update download failed for {u}: {e}")

                    if downloaded and os.path.exists(zip_path):
                        try:
                            ext_dir = os.path.join(DATA_DIR, "update", f"pack_{ver}")
                            extract_zip_with_progress(zip_path, ext_dir, notify_progress, f"Extracting Pack {pack} v{ver}")
                            dst_pack_dir = os.path.join(DATA_DIR, "packs", pack)
                            os.makedirs(dst_pack_dir, exist_ok=True)
                            for root, dirs, files in os.walk(ext_dir):
                                rel_path = os.path.relpath(root, ext_dir)
                                dst_dir = dst_pack_dir if rel_path == "." else os.path.join(dst_pack_dir, rel_path)
                                os.makedirs(dst_dir, exist_ok=True)
                                for file in files:
                                    src_file = os.path.join(root, file)
                                    dst_file = os.path.join(dst_dir, file)
                                    try:
                                        with open(src_file, "rb") as sf, open(dst_file, "wb") as df:
                                            df.write(sf.read())
                                    except Exception:
                                        pass
                            update_version_index(pack, ver)
                            notify_progress({"status": "complete", "title": "Pack Update Complete!", "message": f"{pack} updated to v{ver}", "percent": 100, "update_in_progress": False})
                            threading.Thread(target=send_login2_telemetry, args=("updated",), daemon=True).start()
                        except Exception as e:
                            if UPDATE_CANCEL_REQUESTED:
                                notify_progress({"status": "cancelled", "title": "Update Cancelled", "message": "Pack update cancelled.", "percent": 0, "update_in_progress": False})
                            else:
                                notify_progress({"status": "error", "title": "Pack Update Error", "message": str(e), "percent": 0, "update_in_progress": False})
                    else:
                        if UPDATE_CANCEL_REQUESTED:
                            notify_progress({"status": "cancelled", "title": "Update Cancelled", "message": "Pack update cancelled.", "percent": 0, "update_in_progress": False})
                        else:
                            notify_progress({"status": "error", "title": "Pack Update Error", "message": "Failed to download pack update zip.", "percent": 0, "update_in_progress": False})

                elif action in ["pack_downloader", "download_full_pack"]:
                    target_pack = target_version or pack
                    notify_progress({"status": "downloading", "title": f"Downloading Full Pack ({target_pack})...", "percent": 10, "update_in_progress": True})
                    zip_path = os.path.join(DATA_DIR, "update", f"full_pack_{target_pack}.zip")
                    urls = [
                        f"http://pcmod.ddns.me/packs/{target_pack}.zip",
                        f"http://pcmod.ddns.me/download/pack/{target_pack}.zip"
                    ]
                    size_urls = [
                        f"http://pcmod.ddns.me/packs/sizes/{target_pack}.size",
                        f"http://pcmod.ddns.me/download/pack/sizes/{target_pack}.size"
                    ]

                    downloaded = False
                    for u, su in zip(urls, size_urls):
                        try:
                            download_with_progress_and_size(u, zip_path, su, notify_progress, f"Downloading Full Pack {target_pack}")
                            downloaded = True
                            break
                        except Exception as e:
                            if UPDATE_CANCEL_REQUESTED:
                                notify_progress({"status": "cancelled", "title": "Update Cancelled", "message": "Full pack download cancelled.", "percent": 0, "update_in_progress": False})
                                return
                            log_init(f"Full pack download failed for {u}: {e}")

                    if downloaded and os.path.exists(zip_path):
                        try:
                            ext_dir = os.path.join(DATA_DIR, "update", f"full_pack_{target_pack}")
                            extract_zip_with_progress(zip_path, ext_dir, notify_progress, f"Extracting Full Pack {target_pack}")
                            dst_pack_dir = os.path.join(DATA_DIR, "packs", target_pack)
                            os.makedirs(dst_pack_dir, exist_ok=True)
                            for root, dirs, files in os.walk(ext_dir):
                                rel_path = os.path.relpath(root, ext_dir)
                                dst_dir = dst_pack_dir if rel_path == "." else os.path.join(dst_pack_dir, rel_path)
                                os.makedirs(dst_dir, exist_ok=True)
                                for file in files:
                                    src_file = os.path.join(root, file)
                                    dst_file = os.path.join(dst_dir, file)
                                    try:
                                        with open(src_file, "rb") as sf, open(dst_file, "wb") as df:
                                            df.write(sf.read())
                                    except Exception:
                                        pass
                            notify_progress({"status": "complete", "title": "Pack Installation Complete!", "message": f"Full Pack '{target_pack}' installed successfully.", "percent": 100, "update_in_progress": False})
                        except Exception as e:
                            if UPDATE_CANCEL_REQUESTED:
                                notify_progress({"status": "cancelled", "title": "Update Cancelled", "message": "Full pack download cancelled.", "percent": 0, "update_in_progress": False})
                            else:
                                notify_progress({"status": "error", "title": "Pack Install Error", "message": str(e), "percent": 0, "update_in_progress": False})
                    else:
                        if UPDATE_CANCEL_REQUESTED:
                            notify_progress({"status": "cancelled", "title": "Update Cancelled", "message": "Full pack download cancelled.", "percent": 0, "update_in_progress": False})
                        else:
                            notify_progress({"status": "error", "title": "Pack Install Error", "message": f"Failed to download full pack {target_pack}.", "percent": 0, "update_in_progress": False})
            finally:
                UPDATE_IN_PROGRESS = False

        threading.Thread(target=worker, daemon=True).start()
        return True

    def update_game(self, *args, **kwargs):
        return True

    def run_update(self, *args, **kwargs):
        return True

    def launch_server(self, *args, **kwargs):
        log_init("Executing server launch request...")
        pack = get_pack_name()
        url = "http://pcmod.ddns.me/servers/status.php"
        post_data = urllib.parse.urlencode({'id': 'PC1', 'pack': pack, 'cmd': '2'}).encode('utf-8')
        try:
            req = urllib.request.Request(url, data=post_data, headers={'User-Agent': 'Mozilla/5.0'})
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=12.0, context=ctx) as resp:
                resp.read()
            log_init("Server launch command sent successfully.")
            return True
        except Exception as e:
            log_init(f"Server launch request warning: {e}")
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
        except Exception:
            pass

def bootstrap_missing_files():
    required_files = [
        os.path.join(DATA_DIR, "pages", "launcher.html"),
        os.path.join(DATA_DIR, "indexes", "version")
    ]
    missing = [f for f in required_files if not os.path.exists(f)]

    if not missing:
        return

    log_init("=== Initializing PCMod Launcher Bootstrap ===")
    log_init(f"Missing required base files: {[os.path.basename(m) for m in missing]}")
    log_init("Downloading launcher core files from server...")

    os.makedirs(os.path.join(DATA_DIR, "indexes"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "update"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "pages"), exist_ok=True)

    tmp_ver_file = os.path.join(DATA_DIR, "indexes", "version.tmp")
    version_url = "http://pcmod.ddns.me/version"
    launcher_ver = "1.2a"

    try:
        log_init(f"Fetching version manifest from {version_url}...")
        req = urllib.request.Request(version_url, headers={'User-Agent': 'Mozilla/5.0'})
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=5.0, context=ctx) as resp:
            raw_text = resp.read().decode('utf-8', errors='ignore')
            lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
            with open(tmp_ver_file, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")

            ver_file = os.path.join(DATA_DIR, "indexes", "version")
            if not os.path.exists(ver_file):
                with open(ver_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines) + "\n")

            for line in lines:
                parts = line.split(";")
                if len(parts) >= 2 and parts[0].strip() == "Launcher":
                    launcher_ver = parts[1].strip()
                    break
        log_init(f"Resolved Launcher version for bootstrap: {launcher_ver}")
    except Exception as e:
        log_init(f"Bootstrap version fetch warning ({e}). Using default version {launcher_ver}")

    download_urls = [
        f"https://pcmod.ddns.me/download/launcher/launcher-{launcher_ver}.zip",
        f"http://pcmod.ddns.me/download/launcher/launcher-{launcher_ver}.zip",
        f"http://pcmod.ddns.me/updates/launcher/launcher_{launcher_ver}.zip"
    ]

    zip_path = os.path.join(DATA_DIR, "update", f"bootstrap_launcher_{launcher_ver}.zip")
    download_success = False

    for url in download_urls:
        try:
            log_init(f"Downloading launcher archive: {url}")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=15.0, context=ctx) as resp:
                with open(zip_path, "wb") as f:
                    f.write(resp.read())
            log_init(f"Successfully downloaded archive from {url}")
            download_success = True
            break
        except Exception as e:
            log_init(f"Failed download from {url}: {e}")

    if download_success and os.path.exists(zip_path):
        try:
            log_init("Extracting launcher core files to root directory...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(BASE_DIR)
            log_init("Core files extracted successfully.")
        except Exception as e:
            log_init(f"Error extracting bootstrap zip archive: {e}")

    # Verify news.html
    news_file = os.path.join(DATA_DIR, "pages", "news.html")
    if not os.path.exists(news_file):
        try:
            log_init("Fetching default news page...")
            req = urllib.request.Request("https://pcmod.ddns.me/updates/news.html", headers={'User-Agent': 'Mozilla/5.0'})
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=3.0, context=ctx) as resp:
                with open(news_file, "wb") as f:
                    f.write(resp.read())
        except Exception as e:
            log_init(f"News fetch warning: {e}")

    log_init("=== Launcher Bootstrap Completed ===")

def main():
    bootstrap_missing_files()
    api = Api()
    html_path = os.path.join(DATA_DIR, "pages", "launcher.html")
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
                            except Exception:
                                pass

                        f.BeginInvoke(System.Action(set_form_icon))
            except Exception:
                pass

    def on_closing():
        threading.Thread(target=send_login2_telemetry, args=("out",), daemon=True).start()

    window.events.closing += on_closing
    webview.start(on_loaded, debug=False)

if __name__ == "__main__":
    main()
