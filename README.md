# PCMod - Custom Minecraft Launcher

**PCMod** is a lightweight, manifest-driven custom Minecraft launcher built in Python. It manages multiple modded and vanilla Minecraft instances using remote `.pak` manifests to dynamically download, sync, and update files. 

By leveraging **PortableMC** under the hood, PCMod handles all Java Runtime Environment (JRE) requirements, asset fetching, and game executions automatically—meaning users do not need to pre-install Java on their systems.

---

## Features

* **Manifest-Driven Mod Syncing**: Uses custom `.pak` files to dynamically download and verify mods per instance.
* **No Java Required**: Integrated with PortableMC to automatically isolate and manage the correct Java environments and vanilla game assets.
* **Webview UI**: Renders launcher interfaces, mod lists, and news updates using lightweight embedded HTML pages via `pywebview`.
* **Offline Authentication**: securely caches session tokens using XOR encryption, allowing offline play if the authentication server is down.
* **Automated Crash Reporting**: Automatically captures game crash logs and securely uploads them via FTP for administrative review.
* **Server Alerts Worker**: Optional background process that triggers system tray notifications and audio alerts when players join the server.

---

## Prerequisites & Installation

PCMod is designed to be highly portable. It will automatically bootstrap its own core files (like the HTML frontend) from the server if they are missing upon first launch.

### Requirements
* **Python 3.8+**
* **pywebview** (`pip install pywebview`)

*(Note: Java is **not** required. The internal PortableMC engine handles JRE download and allocation automatically.)*

### How to Run

1. Clone or download the repository to your local machine.
2. Install the required webview dependency:
   ```bash
   pip install pywebview
   ```
3. Execute the launcher script:
   ```bash
   python PCMod.py
   ```
## Project & Data Structure
The launcher operates out of the `data/` directory, keeping the Git repository lightweight and free of binary mod `.jar` files.
```text
├── PCMod.py          # Core launcher logic, UI bridge, and PortableMC wrapper
├── settings.txt      # Launcher configuration (key=value format)
└── data/             # System runtime data & instance directory
    ├── icons/        # Application graphics and window icons
    ├── indexes/      # Version manifests, skin logs, and encrypted auth cache
    ├── pages/        # HTML UI views (launcher.html, updates.html, modlist.html)
    ├── update/       # Staging area for downloads and update extractions
    └── packs/        # Isolated Minecraft instances
        └── 2-5-x/    # Example modded instance workspace
```
## Configuration (`settings.txt`)
`PCMod.py` reads and writes configuration options using a simple `setting=value` format in `settings.txt`:

| Setting | Default | Description |
| :--- | :--- | :--- |
| `username` | *(Empty)* | Active player profile name |
| `memory` | `6144` | Allocated RAM for Java in Megabytes |
| `pack` | `2-5-x` | Selected instance target directory |
| `shortcut` | `1` | Toggles automatic creation of a desktop shortcut (`PCMod Client.lnk`) |
| `autoserver` | `0` | Auto-connects to the target server upon game launch |
| `log-logins` | `1` | Enables login/launch telemetry reporting to server |
| `lite` | `0` | Disables client-side mods by renaming them to `.disabled` |
| `showconsole` | `0` | Toggles visibility of the command prompt debug window |
| `cleanup_updates` | `1` | Automatically cleans temporary staging files in `data/update/` |
| `server_alerts` | `0` | Enables background worker process for player join notifications |
| `server_alerts_mode` | `1` | Alert notification type (`1` = sound & tray popup, `0` = sound only, `-1` = popup only) |

## Manifest-Driven Instance System (`.pak`)
Mods are excluded from Git to avoid repository bloat. Instead, each pack directory under `data/packs/<pack-name>/` includes a `PCMod-<pack-name>.pak` index file.
### .pak Schema
Each line in a `.pak` file uses a semicolon-delimited 5-field structure:
```text
[Side];[Filename];[VersionAdded];[ModID/DisplayName];[Dependencies]
```
* **Side Flags**:
  * `U`: Universal (Client & Server)
  * `C`: Client-side only
  * `S`: Server-side only
  * `B`: Base Library / Coremod
* **Dependencies**: Set to `#` for none, or list dependencies separated by `+` (e.g., `Mekanism+appliedenergistics`).

`PCMod.py` reads this manifest to compare local files against server manifests, downloading missing `.jar` files into the instance `/mods` folder automatically.