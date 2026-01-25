# wrkmon

**Terminal-based YouTube Music Player** - Listen to music right from your terminal!

A beautiful TUI (Terminal User Interface) for streaming YouTube audio. No browser needed, just your terminal.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![PyPI](https://img.shields.io/pypi/v/wrkmon.svg)

## Features

- Search and stream YouTube audio
- Beautiful terminal interface
- Queue management with shuffle/repeat
- Play history and playlists
- Keyboard-driven controls
- Cross-platform (Windows, macOS, Linux)

## Installation

### pip (Recommended)

```bash
pip install wrkmon
```

> **Note:** You also need mpv installed:
> - Windows: `winget install mpv`
> - macOS: `brew install mpv`
> - Linux: `sudo apt install mpv`

### Quick Install Scripts

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/Umar-Khan-Yousafzai/Wrkmon-TUI-Youtube/main/install.ps1 | iex
```

**macOS / Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/Umar-Khan-Yousafzai/Wrkmon-TUI-Youtube/main/install.sh | bash
```

### Package Managers

```powershell
# Windows (Chocolatey)
choco install wrkmon

# macOS (Homebrew) - coming soon
brew install wrkmon

# Linux (Snap) - coming soon
sudo snap install wrkmon
```

## Usage

```bash
wrkmon              # Launch the TUI
wrkmon search "q"   # Quick search
wrkmon play <id>    # Play a video
wrkmon history      # View history
```

## Keyboard Controls

| Key | Action |
|-----|--------|
| `F1` | Search view |
| `F2` | Queue view |
| `F3` | History view |
| `F4` | Playlists view |
| `F5` | Play / Pause |
| `F6` | Volume down |
| `F7` | Volume up |
| `F8` | Next track |
| `F9` | Stop |
| `F10` | Add to queue |
| `/` | Focus search |
| `Enter` | Play selected |
| `a` | Add to queue |
| `Ctrl+C` | Quit |

## Screenshots

```
┌─────────────────────────────────────────────────────────┐
│  wrkmon                                    [Search]     │
├─────────────────────────────────────────────────────────┤
│  Search: lofi beats                                     │
├─────────────────────────────────────────────────────────┤
│  #   Title                              Channel Duration│
│  1   Lofi Hip Hop Radio               ChilledCow 3:24:15│
│  2   Jazz Lofi Beats                  Lofi Girl 2:45:00│
│  3   Study Music Playlist             Study     1:30:22│
├─────────────────────────────────────────────────────────┤
│  ▶ Now Playing: Lofi Beats              advancement █████░░░░░ 1:23:45 │
│  F1 Search  F2 Queue  F5 Play/Pause  F9 Stop            │
└─────────────────────────────────────────────────────────┘
```

## Requirements

- Python 3.10+
- mpv media player

## Development

```bash
git clone https://github.com/Umar-Khan-Yousafzai/Wrkmon-TUI-Youtube.git
cd Wrkmon-TUI-Youtube
pip install -e ".[dev]"
pytest
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

**Umar Khan Yousafzai**

---

*Enjoy your music!*
