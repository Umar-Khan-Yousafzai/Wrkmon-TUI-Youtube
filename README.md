# wrkmon

**Stream YouTube audio from your terminal** - a beautiful TUI music player that runs anywhere.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
[![PyPI](https://img.shields.io/pypi/v/wrkmon.svg)](https://pypi.org/project/wrkmon/)

wrkmon is a keyboard-driven YouTube audio player built with [Textual](https://github.com/Textualize/textual). Search, queue, and stream music without leaving your terminal. It looks like a developer tool, because it is one.

## Features

- **Search & Stream** - Search YouTube and play audio instantly, no browser required
- **Queue Management** - Build playlists with shuffle, repeat (off/one/all), and drag-to-reorder
- **Play History** - Automatically tracks everything you've listened to
- **Playlists** - Create, import, and export playlists (JSON and M3U formats)
- **Lyrics** - Fetch and display lyrics for the current track (`l`)
- **Download** - Save tracks as MP3 for offline listening (`d`)
- **Autoplay / Radio Mode** - Automatically plays related tracks when queue ends (`a`)
- **Playback Speed** - Adjust speed from 0.25x to 3.0x (`]` / `[`)
- **Focus Mode** - Instantly switch to a clean terminal view (`b`)
- **Themes** - Multiple color themes including GitHub Dark, Dracula, Nord, Matrix (`t`)
- **Sleep Timer** - Set a timer to stop playback automatically
- **Desktop Notifications** - Get notified when tracks change
- **Media Keys** - MPRIS support on Linux, media key support on Windows/macOS
- **Cross-Platform** - Works on Windows, macOS, Linux, WSL, and FreeBSD
- **Resume Playback** - Saves queue and playback position between sessions

## Installation

### Quick Install (Recommended)

**macOS / Linux / WSL:**
```bash
curl -sSL https://raw.githubusercontent.com/Umar-Khan-Yousafzai/Wrkmon-TUI-Youtube/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/Umar-Khan-Yousafzai/Wrkmon-TUI-Youtube/main/install.ps1 | iex
```

The install script automatically detects your OS and package manager, installs mpv if missing, and sets up wrkmon.

### pip

```bash
pip install wrkmon
```

You also need [mpv](https://mpv.io/) installed:

| Platform | Command |
|----------|---------|
| Ubuntu/Debian | `sudo apt install mpv` |
| Fedora | `sudo dnf install mpv` |
| Arch | `sudo pacman -S mpv` |
| macOS | `brew install mpv` |
| Windows | `winget install mpv` |

### Optional: JavaScript Runtime

For better YouTube compatibility, install [deno](https://deno.land/) or [Node.js](https://nodejs.org/). The install script handles this automatically.

## Usage

```bash
wrkmon              # Launch the TUI
wrkmon update       # Check for updates
wrkmon deps         # Check dependencies
```

## Keyboard Controls

### Navigation
| Key | Action |
|-----|--------|
| `F1` | Search view |
| `F2` | Queue view |
| `F3` | History view |
| `F4` | Playlists view |
| `j` / `k` | Move up/down in lists |
| `g` / `G` | Jump to top/bottom |

### Playback
| Key | Action |
|-----|--------|
| `F5` / `Space` | Play / Pause |
| `F6` / `-` | Volume down |
| `F7` / `+` | Volume up |
| `F8` / `n` | Next track |
| `p` | Previous track |
| `F9` / `s` | Stop |
| `m` | Mute / Unmute |
| `r` | Cycle repeat (Off / One / All) |
| `]` / `[` | Speed up / down |

### Features
| Key | Action |
|-----|--------|
| `l` | Show lyrics |
| `d` | Download current track |
| `a` | Toggle autoplay / radio mode |
| `b` | Focus mode |
| `t` | Theme picker |
| `?` | Help screen |
| `F10` | Add to queue |
| `Escape` | Close overlay / go back |
| `Ctrl+C` | Quit |

## Configuration

wrkmon stores its config at:
- **Linux/macOS:** `~/.config/wrkmon/config.toml`
- **Windows:** `%APPDATA%\wrkmon\config.toml`

Example `config.toml`:
```toml
[general]
volume = 80
shuffle = false
repeat_mode = "none"
autoplay = false
notifications = true

[player]
playback_speed = 1.0
prefetch_next = true

[ui]
theme = "github_dark"
show_thumbnails = true

[download]
directory = ""
format = "bestaudio"
```

## Requirements

- **Python 3.10+**
- **mpv** media player
- Optional: deno or Node.js (for better YouTube support)

## Development

```bash
git clone https://github.com/Umar-Khan-Yousafzai/Wrkmon-TUI-Youtube.git
cd Wrkmon-TUI-Youtube
pip install -e ".[dev]"
pytest -v
```

Tests run on Python 3.10, 3.11, and 3.12 across Linux, macOS, and Windows via GitHub Actions CI.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

**Umar Khan Yousafzai** - [GitHub](https://github.com/Umar-Khan-Yousafzai)
