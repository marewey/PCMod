# Repository Instructions & Context for AI Agents (Jules)

## Overview
This repository contains a custom Python-based Minecraft launcher (`PCMod.py`) and its associated multi-instance data structures. The architecture separates binary mod files from Git tracking by using dynamic `.pak` manifests to fetch dependencies at runtime.

---

## Root Files & Core Infrastructure

* **`PCMod.py`**: The primary application logic. Handles manifest parsing, update comparisons, UI rendering via HTML webviews, asset synchronization, and Minecraft Java process execution.
* **`build.bat`**: Windows batch script that compiles `PCMod.py` and bundles its required dependencies into a standalone `PCMod.exe` binary located in the `build/` directory.
* **`settings.txt`**: Local key-value store (`key=value`) managing user preferences and launcher runtime state.

### `settings.txt` Key Definitions
| Key | Description / Values |
| :--- | :--- |
| `shortcut` | Desktop shortcut creation flag (`1` = enabled, `0` = disabled) |
| `autoserver` | Auto-connect to default server on game launch (`1`/`0`) |
| `log-logins` | Enable/disable authentication history logging (`1`/`0`) |
| `lite` | Toggle lightweight rendering mode (`1`/`0`) |
| `showconsole` | Toggle game output console visibility (`1`/`0`) |
| `cleanup_updates` | Automatically purge temporary update downloads (`1`/`0`) |
| `server_alerts` | Toggle server broadcast popups (`1`/`0`) |
| `server_alerts_mode` | Alert display mode identifier |
| `pack` | Directory name of the currently selected instance (e.g., `2-5-x`) |
| `memory` | RAM allocated to Java process in megabytes (e.g., `8000`) |
| `username` | Active profile or system username |
| `autoupdate` | Toggle automatic background update checks (`1`/`0`) |
| `pack-index` | Selected dropdown index for the instance manager |

---

## Data Directory Architecture (`/data`)

The `/data` folder contains dynamic assets, web interfaces, instance storage, and persistent index files:

* **`/data/icons/`**: Graphical assets and application icons.
* **`/data/pages/`**: HTML views rendered inside the launcher window (e.g., `updates.html`).
* **`/data/indexes/`**: System state and cache tracking files:
  * **`version.tmp`**: Temporarily stored remote manifest downloaded from the server to check for pending updates.
  * **`version`**: Local version database file. Updated **only** after an update has completed successfully.
  * **`skindex`**: Cache file tracking player skin update timestamps and states.
* **`/data/packs/`**: Isolated Minecraft instance directories (e.g., `Vanilla/`, `2-5-x/`).

---

## Pack Management & `.pak` Manifest Schema

Each pack folder inside `/data/packs/<pack-name>/` must contain a `PCMod-<pack-name>.pak` file at its root.

### Empty Pack Flags
An empty `.pak` file (e.g., `/data/packs/Vanilla/PCMod-Vanilla.pak`) signals to `PCMod.py` that the instance is installed, valid, and selectable in the launcher UI.

### Modded Pack Schema
Modded instances (e.g., `/data/packs/2-5-x/`) maintain an empty `/mods` directory in Git to prevent repository bloat. All mods are indexed in `PCMod-2-5-x.pak` using a semicolon-delimited (`;`) format per line:

```text
[Side];[Filename];[AddedInVersion];[ModID/DisplayName];[Dependencies]