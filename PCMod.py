import os
import sys
import subprocess
import hashlib
import uuid
import urllib.request
import urllib.parse
import json
import datetime
import re
import shutil
import glob
import platform
import webbrowser
from ftplib import FTP

# Optional import of pywebview to handle cases where it isn't installed yet
try:
    import webview
except ImportError:
    webview = None

# Global reference to active window to prevent circular serialization recursion depth exceeded errors
active_window = None

class PCModAPI:
    def __init__(self):
        self.url = "pcmod.ddns.me"
        self.connection = False

        # Default variables matching settings.bat / launch.bat
        self.user = ""
        self.mcuuid = "00000000-0000-0000-0000-000000000000"
        self.uuid_val = "PC2-NOUUID"
        self.pack = "2-5-x"
        self.pack_index = 0
        self.settings = {
            "autoserver": "0",
            "autoupdate": "1",
            "lite": "0",
            "log-logins": "1",
            "shortcut": "1",
            "showconsole": "0",
            "memory": "4096",
            "pack-index": "0",
            "pack": "2-5-x",
            "debug": "nul"
        }

        # Load user and core vars
        self.load_user_info()
        self.load_settings()
        self.log(f"PCMod Initializing for user: {self.user}")
        self.check_net()
        self.apply_console_visibility(self.settings.get("showconsole", "0"))

    def log(self, msg):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] {msg}"
        print(formatted)
        try:
            log_file = os.path.join("data", "init.log")
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(formatted + "\n")
        except Exception as e:
            print("Failed to write to init.log:", e)

    def apply_console_visibility(self, show_val):
        if platform.system().lower() == "windows":
            try:
                import ctypes
                hwnd = ctypes.windll.kernel32.GetConsoleWindow()
                if hwnd:
                    # 5 = SW_SHOW, 0 = SW_HIDE
                    ctypes.windll.user32.ShowWindow(hwnd, 5 if str(show_val) == "1" else 0)
                    self.log(f"Console visibility set to: {show_val}")
            except Exception as e:
                self.log(f"Error adjusting console visibility: {e}")

    def load_user_info(self):
        user_file = os.path.join("data", "indexes", "user")
        if os.path.exists(user_file):
            try:
                with open(user_file, "r", encoding="utf-8") as f:
                    self.user = f.read().strip()
            except Exception:
                pass
        if not self.user:
            self.user = os.environ.get("USERNAME", "Player")

        uuid_file = os.path.join("data", "indexes", "uuid")
        if os.path.exists(uuid_file):
            try:
                with open(uuid_file, "r", encoding="utf-8") as f:
                    self.uuid_val = f.read().strip()
            except Exception:
                pass
        else:
            import random
            val = random.randint(126735, 126735 + 50000)
            self.uuid_val = f"PC2-{val}{self.user[:1]}0"
            os.makedirs(os.path.dirname(uuid_file), exist_ok=True)
            with open(uuid_file, "w", encoding="utf-8") as f:
                f.write(self.uuid_val)

    def load_settings(self):
        settings_file = "settings.txt"
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line:
                            parts = line.strip().split("=", 1)
                            if len(parts) == 2:
                                self.settings[parts[0]] = parts[1]
            except Exception as e:
                print("Error loading settings:", e)

        self.pack = self.settings.get("pack", "2-5-x")
        try:
            self.pack_index = int(self.settings.get("pack-index", "0"))
        except ValueError:
            self.pack_index = 0

    def save_settings(self):
        settings_file = "settings.txt"
        try:
            with open(settings_file, "w", encoding="utf-8") as f:
                for k, v in self.settings.items():
                    f.write(f"{k}={v}\n")
        except Exception as e:
            print("Error saving settings:", e)

    def check_net(self):
        self.connection = False
        # Fast ping check
        try:
            param = "-n" if platform.system().lower() == "windows" else "-c"
            subprocess.run(["ping", param, "1", "8.8.8.8"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)
            self.connection = True
        except Exception:
            pass

        if self.connection:
            sig_file = os.path.join("data", "indexes", "signature")
            os.makedirs(os.path.dirname(sig_file), exist_ok=True)
            try:
                # Retrieve signature
                sig_url = f"http://{self.url}/updates/sig"
                urllib.request.urlretrieve(sig_url, sig_file)
                with open(sig_file, "r", encoding="utf-8", errors="ignore") as f:
                    sig = f.read().strip()
                if sig == "PCMod":
                    self.connection = True
                else:
                    self.connection = False
            except Exception:
                self.connection = False

    def init_launcher(self):
        self.check_net()
        # Initialize calculations
        self.calculate_default_memory_if_needed()
        self.init_downloads()

        # Pack-specific mod count
        modcount = self.get_mod_count()
        # Fetch versions list
        versions_list, launcher_version, pack_version = self.get_versions_info()
        # Get online players list
        online_players = self.get_online_players_html()

        return {
            "user": self.user,
            "mcuuid": self.mcuuid,
            "uuid": self.uuid_val,
            "settings": self.settings,
            "modcount": modcount,
            "launcher_version": launcher_version,
            "pack_version": pack_version,
            "versions_list": versions_list,
            "online_players": online_players
        }

    def calculate_default_memory_if_needed(self):
        if self.settings.get("memory") and self.settings.get("memory") != "":
            return

        mem_bytes = 0
        if platform.system().lower() == "windows":
            try:
                out = subprocess.check_output(["wmic", "computersystem", "get", "TotalPhysicalMemory"], stderr=subprocess.PIPE)
                lines = out.decode('utf-8', errors='ignore').strip().split('\n')
                if len(lines) >= 2:
                    mem_bytes = int(lines[1].strip())
            except Exception:
                pass

        if mem_bytes == 0:
            mem_gb = 8
        else:
            mem_gb = mem_bytes // 1073741824

        # formula: 3584+(64*mem_gb)
        calculated_memory = 3584 + (64 * mem_gb)
        self.settings["memory"] = str(calculated_memory)
        self.save_settings()

    def init_downloads(self):
        if not self.connection:
            return
        print("Downloading News, servers.dat, script.zs...")
        try:
            # News.html
            news_url = f"http://{self.url}/updates/news.html"
            news_path = os.path.join("data", "pages", "news.html")
            os.makedirs(os.path.dirname(news_path), exist_ok=True)
            urllib.request.urlretrieve(news_url, news_path)
        except Exception as e:
            print("News download failed:", e)

        try:
            # Script.zs
            script_path = os.path.join("data", "packs", self.pack, "scripts", "script.zs")
            if os.path.exists(os.path.dirname(script_path)):
                script_url = f"http://{self.url}/updates/pack/scripts/script_{self.pack}.zs"
                urllib.request.urlretrieve(script_url, script_path)
        except Exception as e:
            print("script.zs download failed:", e)

        try:
            # Servers.dat
            servers_path = os.path.join("data", "packs", self.pack, "servers.dat")
            if os.path.exists(os.path.dirname(servers_path)):
                servers_url = f"http://{self.url}/updates/pack/servers/servers_{self.pack}.dat"
                urllib.request.urlretrieve(servers_url, servers_path)
        except Exception as e:
            print("servers.dat download failed:", e)

    def get_mod_count(self):
        modcount_file = os.path.join("data", "indexes", "modcount")
        # Direct folder file counts is extremely reliable
        mods_dir = os.path.join("data", "packs", self.pack, "mods")
        if os.path.exists(mods_dir):
            mods = [f for f in os.listdir(mods_dir) if f.endswith(".jar")]
            count = len(mods)
            os.makedirs(os.path.dirname(modcount_file), exist_ok=True)
            with open(modcount_file, "w", encoding="utf-8") as f:
                f.write(str(count))
            return count
        return "--"

    def get_versions_info(self):
        versions_file = os.path.join("data", "indexes", "version")
        versions_list = []
        launcher_version = "1.2a"
        pack_version = "2.5.3a"

        if os.path.exists(versions_file):
            try:
                with open(versions_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        parts = line.strip().split(";")
                        if len(parts) >= 2:
                            name = parts[0]
                            version_str = parts[1]
                            if name == "Launcher":
                                launcher_version = version_str
                            else:
                                # Standard HTA filter: only show if the pack actually exists locally
                                pack_dir = os.path.join("data", "packs", name)
                                pak_file = os.path.join(pack_dir, f"PCMod-{name}.pak")
                                if os.path.exists(pak_file) or name == "Vanilla":
                                    versions_list.append({"name": name, "version": version_str})
                                if name == self.pack:
                                    pack_version = version_str
            except Exception as e:
                print("Error parsing version file:", e)

        return versions_list, launcher_version, pack_version

    def get_online_players_html(self):
        online_file = os.path.join("data", "indexes", "online")
        if self.connection:
            try:
                url = f"http://{self.url}/players/list-{self.pack}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    html = resp.read().decode('utf-8', errors='ignore').strip()
                    os.makedirs(os.path.dirname(online_file), exist_ok=True)
                    with open(online_file, "w", encoding="utf-8") as f:
                        f.write(html)
                    return html
            except Exception:
                pass
        # Fallback to local
        if os.path.exists(online_file):
            try:
                with open(online_file, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            except Exception:
                pass
        return "Offline/No Connection"

    def get_offline_uuid(self, username):
        val = hashlib.md5(f"OfflinePlayer:{username}".encode('utf-8')).digest()
        b = list(val)
        b[6] = (b[6] & 0x0f) | 0x30
        b[8] = (b[8] & 0x3f) | 0x80
        return str(uuid.UUID(bytes=bytes(b)))

    def get_java_runtime(self):
        # Try finding under data/packs/*/jvm/java*/bin/java.exe
        jvm_pattern = os.path.join("data", "packs", "*", "jvm", "java*", "bin", "java.exe")
        matches = glob.glob(jvm_pattern)
        if matches:
            return matches[0]
        # Check system java
        try:
            subprocess.run(["java", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return "java"
        except Exception:
            return None

    def get_mcuuid(self):
        mcuuid_file = os.path.join("data", "indexes", "mcuuid")
        jar_path = os.path.join("bin", "uuid-tool-1.0.jar")
        java_exe = self.get_java_runtime()
        mcuuid = ""

        if os.path.exists(jar_path) and java_exe:
            try:
                p = subprocess.Popen([java_exe, "-jar", jar_path, "-o"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, _ = p.communicate(input=f"{self.user}\r\n".encode('utf-8'))
                out_str = out.decode('utf-8', errors='ignore').strip()
                parts = out_str.split()
                if len(parts) >= 2 and parts[0] == self.user:
                    mcuuid = parts[1].replace("-", "")
            except Exception as e:
                print("Error running uuid-tool jar:", e)

        if not mcuuid:
            mcuuid = self.get_offline_uuid(self.user).replace("-", "")

        os.makedirs(os.path.dirname(mcuuid_file), exist_ok=True)
        with open(mcuuid_file, "w", encoding="utf-8") as f:
            f.write(mcuuid)

        self.mcuuid = mcuuid
        return mcuuid

    def decode_auth_token(self, username):
        auth_file = os.path.join("data", "indexes", "auth")
        if not os.path.exists(auth_file):
            return ""
        xcode_path = os.path.join("bin", "xcode.exe")
        if os.path.exists(xcode_path) and os.name == 'nt':
            try:
                p = subprocess.Popen([xcode_path, auth_file], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p.communicate(input=f"{username}\r\n".encode('utf-8'))
                with open(auth_file, "r", encoding="utf-8", errors="ignore") as f:
                    token = f.read().strip().split()[0]
                # re-encrypt back
                p = subprocess.Popen([xcode_path, auth_file], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p.communicate(input=f"{username}\r\n".encode('utf-8'))
                return token
            except Exception as e:
                print("Error with xcode token:", e)
        # Fallback raw read
        try:
            with open(auth_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().strip().split()
                return content[0] if content else ""
        except Exception:
            return ""

    def rot13_5_decode(self, text):
        mapping = {}
        for i in range(26):
            mapping[chr(65 + i)] = chr(65 + (i + 13) % 26)
            mapping[chr(97 + i)] = chr(97 + (i + 13) % 26)
        for i in range(10):
            mapping[chr(48 + i)] = chr(48 + (i + 5) % 10)
        return "".join(mapping.get(c, c) for c in text)

    def open_modlist(self):
        global active_window
        self.generate_modlist_page()
        modlist_path = os.path.abspath(os.path.join("data", "pages", "modlist.html"))
        if active_window and webview:
            # Open in a pywebview window
            webview.create_window("PCMod - Modlist", f"file:///{modlist_path}", width=800, height=600)
        else:
            webbrowser.open(f"file:///{modlist_path}")

    def generate_modlist_page(self):
        pak_file = os.path.join("data", "packs", self.pack, f"PCMod-{self.pack}.pak")
        if not os.path.exists(pak_file):
            return

        mods = []
        try:
            with open(pak_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    parts = line.strip().split(";")
                    if len(parts) >= 4:
                        tag, filename, version, modname = parts[0], parts[1], parts[2], parts[3]
                        additional = parts[4] if len(parts) >= 5 else "#"
                        mods.append({
                            "tag": tag,
                            "file": filename,
                            "version": version,
                            "name": modname,
                            "additional": additional
                        })
        except Exception as e:
            print("Error reading pak file:", e)
            return

        html_file = os.path.join("data", "pages", "modlist.html")
        os.makedirs(os.path.dirname(html_file), exist_ok=True)

        lite_enabled = (self.settings.get("lite", "0") == "1")

        # Draw the page
        html_out = [
            "<html><head>",
            "<style>",
            "body { background-color: #5d6d7e; font-family: sans-serif; color: #111; }",
            ".altext { display: none; }",
            "label:hover .altext { display: inline-block; }",
            "th { background-color: #34495e; color: #fff; padding: 10px; }",
            "td { padding: 8px; }",
            "</style></head>",
            "<body><center>",
            "<h2>PCMod Pack Modlist</h2>",
            "<table border='1' style='background-color: #BCF6F6; border-collapse: collapse;'>",
            "<tr><th>Mod Name</th><th>Required</th><th>Version Added/Updated</th></tr>"
        ]

        for m in mods:
            if m["tag"] == "D":
                continue
            side = "Universally"
            color = "background-color:#BCF6F6;"
            if m["tag"] == "U":
                side = "Universally" if m["additional"] == "#" else "Universally*"
                color = "background-color:#BCF6F6;" if m["additional"] == "#" else "background-color:#A9DDDD;"
            elif m["tag"] == "C":
                side = "Client-Side" if m["additional"] == "#" else "Client-Side*"
                color = "background-color:#CCF1C1;" if m["additional"] == "#" else "background-color:#B7D8AD;"
                if lite_enabled:
                    color += "text-decoration: line-through;"
            elif m["tag"] == "B":
                side = "Core Mod"
                color = "background-color:#FFAFA6;"

            tmp = m["name"]
            if m["additional"] != "#":
                tmp = f"{m['name']} [{m['additional']}]"

            tmp_a = tmp[:48]
            tmp_b = tmp[48:]

            html_out.append(f"<tr><td style='{color}'><label>{tmp_a}<span class='altext'>{tmp_b}</span></label></td>")
            html_out.append(f"<td style='{color}'><label>{side}</label></td>")
            html_out.append(f"<td style='{color}'><label>{m['version']}</label></td></tr>")

        html_out.append("</table></center></body></html>")

        fixed_html = "\n".join(html_out)
        try:
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(fixed_html)
        except Exception as e:
            print("Error generating modlist html:", e)

    def open_web(self, site):
        urls = {
            "discord": "https://discord.gg/AJaVhvR",
            "pcmod": "http://pcmod.ddns.me",
            "auth": "http://pcmod.ddns.me/account"
        }
        url = urls.get(site)
        if url:
            webbrowser.open(url)

    def refresh_players(self):
        return self.get_online_players_html()

    def set_setting(self, key, value):
        self.settings[key] = value
        self.save_settings()
        self.log(f"Setting updated: {key} = {value}")

        if key == "shortcut":
            self.manage_shortcut(value)
        elif key == "showconsole":
            self.apply_console_visibility(value)

    def get_windows_desktop(self):
        if platform.system().lower() != "windows":
            return None
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
            val, _ = winreg.QueryValueEx(key, "Desktop")
            winreg.CloseKey(key)
            return os.path.expandvars(val)
        except Exception:
            return os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")

    def manage_shortcut(self, enable):
        if platform.system().lower() != "windows":
            return

        desktop_dir = self.get_windows_desktop()
        if not desktop_dir or not os.path.exists(desktop_dir):
            desktop_dir = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")

        shortcut_lnk = os.path.join(desktop_dir, "PCMod.lnk")
        start_menu_dir = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Plattecraft")
        start_menu_lnk = os.path.join(start_menu_dir, "PCMod.lnk")

        if enable == "1":
            print("Creating desktop and start menu shortcuts...")
            target_path = os.path.abspath("checkpy.bat")
            working_dir = os.path.abspath(".")
            icon_path = os.path.abspath(os.path.join("data", "icons", "icon.ico"))

            # PowerShell script to create shortcut robustly without VBScript blocking
            safe_lnk = shortcut_lnk.replace("'", "''")
            safe_target = target_path.replace("'", "''")
            safe_working = working_dir.replace("'", "''")
            safe_icon = icon_path.replace("'", "''")
            ps_cmd = f"""
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut('{safe_lnk}')
            $Shortcut.TargetPath = '{safe_target}'
            $Shortcut.WorkingDirectory = '{safe_working}'
            $Shortcut.Description = 'PCMod - Plattecraft Modded Launcher'
            $Shortcut.IconLocation = '{safe_icon}'
            $Shortcut.Save()
            """
            try:
                subprocess.run(["powershell", "-Command", ps_cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # Copy to start menu
                os.makedirs(start_menu_dir, exist_ok=True)
                if os.path.exists(shortcut_lnk):
                    shutil.copy(shortcut_lnk, start_menu_lnk)
            except Exception as e:
                print("Error creating shortcut:", e)
        else:
            print("Deleting shortcuts...")
            if os.path.exists(shortcut_lnk):
                try: os.remove(shortcut_lnk)
                except Exception: pass
            if os.path.exists(start_menu_lnk):
                try: os.remove(start_menu_lnk)
                except Exception: pass

    def show_message(self, title, message):
        safe_msg = message.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "")
        if active_window:
            active_window.evaluate_js(f"alert('{safe_msg}');")

    def show_confirmation(self, title, message):
        safe_msg = message.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "")
        if active_window:
            return active_window.evaluate_js(f"confirm('{safe_msg}');")
        return False

    def set_lite_mode(self, val):
        self.settings["lite"] = val
        self.save_settings()

        # Execute file moves for Lite mode
        pak_file = os.path.join("data", "packs", self.pack, f"PCMod-{self.pack}.pak")
        if not os.path.exists(pak_file):
            return

        mods_dir = os.path.join("data", "packs", self.pack, "mods")
        disabled_dir = os.path.join("data", "disabledclimods")
        os.makedirs(mods_dir, exist_ok=True)
        os.makedirs(disabled_dir, exist_ok=True)

        # Read the client mods to disable/enable
        client_mods = []
        try:
            with open(pak_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    parts = line.strip().split(";")
                    if len(parts) >= 2 and parts[0] == "C":
                        client_mods.append(parts[1])
        except Exception as e:
            print("Lite mode list read error:", e)
            return

        special_client_mods = [
            "OptiFineHDUHpre", "Offline Skins", "Controlling", "darkness",
            "betterbiomeblend", "EntityCollisionFPSFix", "entityculling"
        ]

        if val == "1":
            # Switch to Lite mode: move client-side mods out to disabledclimods
            for filename in client_mods:
                src = os.path.join(mods_dir, filename)
                dst = os.path.join(disabled_dir, filename)
                if os.path.exists(src):
                    is_special = False
                    for special in special_client_mods:
                        if special.lower() in filename.lower():
                            is_special = True
                            break
                    if not is_special:
                        try:
                            shutil.move(src, dst)
                        except Exception:
                            pass
            self.show_message("PCMod Modes", "Switched to Lite Mode successfully.")
        else:
            # Switch to default mode: move all disabled client-side mods back
            for filename in os.listdir(disabled_dir):
                src = os.path.join(disabled_dir, filename)
                dst = os.path.join(mods_dir, filename)
                if os.path.exists(src):
                    try:
                        shutil.move(src, dst)
                    except Exception:
                        pass
            self.show_message("PCMod Modes", "Switched to Default Mode successfully.")

    def set_memory(self, val):
        self.settings["memory"] = val
        self.save_settings()

    def set_version_select(self, val):
        parts = val.split(" ", 1)
        if len(parts) == 2:
            self.pack_index = int(parts[0])
            self.pack = parts[1]
            self.settings["pack-index"] = str(self.pack_index)
            self.settings["pack"] = self.pack
            self.save_settings()

            # Recalculate mod count
            self.get_mod_count()

    def save_settings_btn(self):
        self.save_settings()
        self.show_message("PCMod Settings", "Settings saved successfully!")

    def launch_server(self):
        if self.connection:
            try:
                url = f"http://{self.url}/servers/status.php"
                data = urllib.parse.urlencode({'id': 'PC1', 'pack': self.pack, 'cmd': '2'}).encode('utf-8')
                req = urllib.request.Request(url, data=data, headers={'User-Agent': 'Mozilla/5.0'})
                urllib.request.urlopen(req, timeout=5)
                self.show_message("PCMod", "Server launch requested successfully.")
            except Exception as e:
                print("Launch server request failed:", e)
                self.show_message("PCMod Error", "Server launch request failed.")

    def login(self, username, password):
        self.log(f"Login attempt initiated for user '{username}'")
        res = self.login_auth_flow(username, password)
        self.log(f"Login auth flow result: {res}")
        if res["status"] == "success":
            self.show_message("PCMod Login", "Logged In Successfully.")
        else:
            if res["auth"] == "401.auth":
                self.show_message("PCMod Error", "Password was incorrect. Try again.\nTo reset password, go to pcmod.ddns.me/account")
            else:
                self.show_message("PCMod Error", f"Login failed. Return code: {res['auth']}")
        return res

    def login_auth_flow(self, username, password):
        md5_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
        self.log(f"Computed password MD5 hash: '{md5_hash}'")

        auth_file = os.path.join("data", "indexes", "auth")
        os.makedirs(os.path.dirname(auth_file), exist_ok=True)

        with open(auth_file, "wb") as f:
            f.write(f"{md5_hash}\r\n".encode('utf-8'))

        xcode_path = os.path.join("bin", "xcode.exe")
        if os.path.exists(xcode_path) and os.name == 'nt':
            try:
                self.log(f"Encrypting {auth_file} using xcode.exe for user '{username}'...")
                p = subprocess.Popen([xcode_path, auth_file], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate(input=f"{username}\r\n".encode('utf-8'))
                self.log(f"xcode encryption output: {out.decode('utf-8', errors='ignore').strip()}")
            except Exception as e:
                self.log(f"xcode encryption error: {e}")

        token = self.decode_auth_token(username)
        self.log(f"Decoded token from file: '{token}'")
        if not token:
            token = md5_hash
            self.log(f"Fallback token used: '{token}'")

        if not token.startswith("\\"):
            token = "\\" + token
            self.log(f"Prepended leading backslash for server auth match: '{token}'")

        return_auth = "404.auth"

        if self.connection:
            try:
                auth_url = f"http://{self.url}/commands/authp.php"
                post_data = {'x': token, 'u': username, 'z': 'auth'}
                self.log(f"Submitting auth POST to '{auth_url}' with data: {post_data}")
                data = urllib.parse.urlencode(post_data).encode('utf-8')
                req = urllib.request.Request(auth_url, data=data, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    return_auth = resp.read().decode('utf-8', errors='ignore').strip()
                self.log(f"Server auth response: '{return_auth}'")
            except Exception as e:
                self.log(f"Auth HTTP call failed: {e}")
                return_auth = "408.auth"
        else:
            self.log("No internet connection available for auth check.")
            return_auth = "408.auth"

        if return_auth in ["200.auth", "404.auth"]:
            user_file = os.path.join("data", "indexes", "user")
            with open(user_file, "w", encoding="utf-8") as f:
                f.write(username)
            self.user = username
            self.get_mcuuid()
            return {"status": "success", "auth": return_auth}
        else:
            return {"status": "error", "auth": return_auth}

    def launch_game(self):
        global active_window
        # Starts portablemc and detaches session
        print("Launching the game...")

        # Step 1: skinget
        self.skinget()

        # Step 2: mcuuid
        self.get_mcuuid()

        # Step 3: log login IN
        if self.settings.get("log-logins", "1") == "1":
            self.log_login_server("in")

        # Step 4: crash reports initial count
        crash_reports_dir = os.path.join("data", "packs", self.pack, "crash-reports")
        initial_crashes = set(os.listdir(crash_reports_dir)) if os.path.exists(crash_reports_dir) else set()

        # Hide the launcher window if run via webview
        if active_window:
            active_window.hide()

        # Run PortableMC
        modloader = "forge"
        mcversion = "1.19.2"
        mlversion = "43.3.5"

        versions_file = os.path.join("data", "indexes", "version")
        if os.path.exists(versions_file):
            try:
                with open(versions_file, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split(";")
                        if len(parts) >= 5 and parts[0] == self.pack:
                            modloader = parts[2]
                            mcversion = parts[3]
                            mlversion = parts[4]
            except Exception:
                pass

        m_version = f"{modloader}:{mcversion}-{mlversion}"
        if modloader.lower() == "vanilla":
            m_version = mcversion
        elif modloader.lower() == "fabric":
            m_version = f"fabric:{mcversion}:{mlversion}"
        elif modloader.lower() == "#-btw":
            m_version = mlversion

        # Auto server
        autoserver_args = []
        if self.settings.get("autoserver", "0") == "1":
            ports = {
                "2-5-x": "25565",
                "2-4-x": "25566",
                "BTW": "25568",
                "2-3-x": "25567"
            }
            port = ports.get(self.pack, "25566")
            autoserver_args = ["--server", "plattecraft.ddns.net", "--server-port", port]

        memory = self.settings.get("memory", "4096")
        jvm_args = f"-Xmx{memory}M -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M"

        # Check portablemc executable path
        portablemc_cmd = ["portablemc"]
        pmc_local = os.path.join("bin", "pmc", "bin", "portablemc")
        if not shutil.which("portablemc"):
            if os.path.exists(pmc_local):
                portablemc_cmd = [sys.executable, pmc_local] if not pmc_local.endswith(".exe") else [pmc_local]
            else:
                # Install it via pip dynamically as redundancy
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "portablemc"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except Exception:
                    pass
                portablemc_cmd = [sys.executable, "-m", "portablemc"]

        # Command
        work_dir = os.path.abspath(os.path.join("data", "packs", self.pack))
        cmd = portablemc_cmd + [
            "--work-dir", work_dir,
            "--main-dir", work_dir,
            "start", "-u", self.user, "-i", self.mcuuid
        ] + autoserver_args + [
            f"--jvm-args={jvm_args}",
            m_version
        ]

        print("Executing command:", " ".join(cmd))

        try:
            # Run the process
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.communicate() # wait for launch exit
        except Exception as e:
            print("Launch failed:", e)

        # Post launch exit
        if active_window:
            active_window.show()

        # Crash detection
        final_crashes = set(os.listdir(crash_reports_dir)) if os.path.exists(crash_reports_dir) else set()
        new_crashes = final_crashes - initial_crashes
        if new_crashes:
            print("Crash detected!")
            self.handle_crash_upload(list(new_crashes)[0])

        if self.settings.get("log-logins", "1") == "1":
            self.log_login_server("out")

    def log_login_server(self, state):
        if not self.connection:
            return
        xip = "xxx.xxx.xxx.xxx"
        try:
            req = urllib.request.Request("https://ifconfig.co", headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as resp:
                xip = resp.read().decode('utf-8', errors='ignore').strip()
        except Exception:
            pass

        versions_list, launcher_version, pack_version = self.get_versions_info()
        modcount = self.get_mod_count()
        memory = self.settings.get("memory", "4096")

        url = f"http://{self.url}/commands/login2.php"
        data = urllib.parse.urlencode({
            'user': self.user,
            'uuid': self.uuid_val,
            'state': state,
            'mcuuid': self.mcuuid,
            'version': f"{self.pack}/{pack_version}",
            'lversion': launcher_version,
            'netinfo': xip,
            'modcount': modcount,
            'memory': memory
        }).encode('utf-8')

        try:
            req = urllib.request.Request(url, data=data, headers={'User-Agent': 'Mozilla/5.0'})
            urllib.request.urlopen(req, timeout=5)

            cli_url = f"http://{self.url}/commands/climsg2.php"
            cli_state = "launched" if state == "in" else "crashed" if state == "crash" else "closed"
            cli_data = urllib.parse.urlencode({
                'user': self.user,
                'state': cli_state,
                'pack': self.pack
            }).encode('utf-8')
            req_cli = urllib.request.Request(cli_url, data=cli_data, headers={'User-Agent': 'Mozilla/5.0'})
            urllib.request.urlopen(req_cli, timeout=5)
        except Exception as e:
            print("Login logger failed:", e)

    def handle_crash_upload(self, crash_file):
        global active_window
        crash_reports_dir = os.path.join("data", "packs", self.pack, "crash-reports")
        crash_path = os.path.join(crash_reports_dir, crash_file)

        if self.settings.get("log-logins", "1") == "1":
            self.log_login_server("crash")

        try:
            os.startfile(crash_reports_dir)
        except Exception:
            pass

        ftppass_enc = "cpzbqsgc"
        ftppass = self.rot13_5_decode(ftppass_enc)

        if self.connection:
            print("Uploading crash report to server...")
            try:
                ftp = FTP(self.url, timeout=10)
                ftp.login(user="pcmod", password=ftppass)

                try:
                    ftp.cwd("logins")
                except Exception:
                    pass
                try:
                    ftp.cwd(self.user)
                except Exception:
                    try:
                        ftp.mkd(self.user)
                        ftp.cwd(self.user)
                    except Exception:
                        pass
                try:
                    ftp.mkd("crash-reports")
                except Exception:
                    pass
                try:
                    ftp.cwd("crash-reports")
                except Exception:
                    pass

                with open(crash_path, "rb") as f:
                    ftp.storbinary(f"STOR {crash_file}", f)

                ftp.quit()
                print("Crash report upload completed!")
                self.show_message("PCMod Error", "Minecraft has crashed. The crashreport was successfully sent to the server for examination.")
            except Exception as e:
                print("FTP Crash upload failed:", e)

    def run_update(self):
        print("Launching update process...")
        try:
            # Replicate exact settings.bat update sequence natively
            shutil.copy(os.path.join("cmd", "update.bat"), os.path.join("cmd", "update_.bat"))
            if platform.system().lower() == "windows":
                # Start cmd/update_.bat empty in a visible console window (HTA behaviour)
                subprocess.Popen(["cmd.exe", "/c", "call", "cmd\\update_.bat", "empty"], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                print("Self-update console launch is only supported on Windows.")
        except Exception as e:
            print("Error executing updater:", e)

    def skinget(self):
        if not self.connection:
            return
        print("Checking/Getting skins...")
        try:
            skindex_file = os.path.join("data", "indexes", "skindex")
            os.makedirs(os.path.dirname(skindex_file), exist_ok=True)
            urllib.request.urlretrieve(f"http://{self.url}/skins/skin.index", skindex_file)

            skins = {}
            with open(skindex_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        skins[parts[0]] = parts[1]

            skins_dir = os.path.join("data", "packs", self.pack, "cachedImages", "skins")
            os.makedirs(skins_dir, exist_ok=True)

            for skin_name, version in skins.items():
                # Sanitize skin_name to prevent directory traversal vulnerability
                safe_skin_name = os.path.basename(skin_name)
                dest = os.path.join(skins_dir, f"{safe_skin_name}.png")
                if not os.path.exists(dest):
                    print(f"Downloading skin: {safe_skin_name}")
                    urllib.request.urlretrieve(f"http://{self.url}/skins/{urllib.parse.quote(skin_name)}", dest)
        except Exception as e:
            print("Skinget error:", e)

def set_window_icon():
    if platform.system().lower() == "windows":
        icon_path = os.path.abspath(os.path.join("data", "icons", "icon.ico"))
        if os.path.exists(icon_path):
            try:
                import ctypes
                h_icon = ctypes.windll.user32.LoadImageW(
                    0, icon_path, 1, 0, 0, 0x0010 | 0x0080
                )
                if h_icon:
                    def enum_windows_cb(hwnd, extra):
                        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                        buff = ctypes.create_unicode_buffer(length + 1)
                        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                        if "PCMod Launcher" in buff.value:
                            ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, h_icon)
                            ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, h_icon)
                        return True

                    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
                    ctypes.windll.user32.EnumWindows(WNDENUMPROC(enum_windows_cb), 0)
            except Exception as e:
                print("Error setting icon:", e)

def start_launcher():
    global active_window
    if not webview:
        print("Error: pywebview is not installed. Please install it using 'pip install pywebview'")
        return

    launcher_html = os.path.abspath(os.path.join("data", "pages", "launcher.html"))
    if not os.path.exists(launcher_html):
        print(f"Error: Launcher HTML file not found at {launcher_html}")
        return

    api = PCModAPI()
    window = webview.create_window(
        title="PCMod Launcher",
        url=f"file:///{launcher_html}",
        width=1100,
        height=655,
        resizable=True,
        js_api=api
    )
    active_window = window

    def on_loaded():
        set_window_icon()

    webview.start(on_loaded)

if __name__ == "__main__":
    start_launcher()
