# wrkmon 🎵

**Stealth TUI YouTube Audio Player** - Stream music while looking productive!

A terminal-based YouTube audio player that runs completely hidden in the background. No visible windows, no distractions - just music.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

## Features

- 🔍 **YouTube Search** - Search and stream any YouTube audio
- 👻 **Stealth Mode** - No visible windows, completely hidden playback
- 🎨 **Beautiful TUI** - Clean terminal interface with keyboard controls
- 📋 **Queue Management** - Add tracks, shuffle, repeat
- 📜 **History & Playlists** - Track your listening history
- ⌨️ **Keyboard Driven** - Full control without touching the mouse
- 🖥️ **Cross-Platform** - Works on Windows, macOS, and Linux

## Installation

### Quick Install (Recommended)

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/Umar-Khan-Yousafzai/Wrkmon-TUI-Youtube/main/install.ps1 | iex
```

**macOS / Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/Umar-Khan-Yousafzai/Wrkmon-TUI-Youtube/main/install.sh | bash
```

### Package Managers

**Windows (Chocolatey):**
```powershell
choco install wrkmon
```

**Windows (winget):**
```powershell
winget install wrkmon
```

**macOS (Homebrew):**
```bash
brew install wrkmon
```

**Linux (Snap):**
```bash
sudo snap install wrkmon
```

**Linux (apt):**
```bash
sudo apt install wrkmon
```

### pip (All Platforms)

```bash
pip install wrkmon
```

> **Note:** If using pip, you need to install mpv separately:
> - Windows: `winget install mpv` or `choco install mpv`
> - macOS: `brew install mpv`
> - Linux: `sudo apt install mpv`

## Usage

```bash
wrkmon              # Launch the TUI
wrkmon search "q"   # Quick search from terminal
wrkmon play <id>    # Play a specific video
wrkmon history      # View play history
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
| `a` | Add to queue (in list) |
| `Ctrl+C` | Quit |

## Screenshots

```
┌─────────────────────────────────────────────────────────┐
│  wrkmon                                    [Search]     │
├─────────────────────────────────────────────────────────┤
│  Search: lofi hip hop                                   │
├─────────────────────────────────────────────────────────┤
│  #   Process                          PID   Duration    │
│  1   node_worker_847291              8472   3:24:15     │
│  2   webpack_compile_process         9123   2:45:00     │
│  3   eslint_daemon_runner            7834   1:30:22     │
├─────────────────────────────────────────────────────────┤
│  ▶ Now Playing: lofi hip hop beats    advancement █████░░░░░ 1:23:45 │
│  F1 Search  F2 Queue  F5 Play/Pause  F9 Stop            │
└─────────────────────────────────────────────────────────┘
```

## Why wrkmon?

Ever wanted to listen to music at work but worried about monitoring software catching you? wrkmon disguises itself as a legitimate development process while streaming your favorite tunes in the background. The TUI looks like a process monitor, and the audio plays through mpv with no visible windows.

## Requirements

- Python 3.10+
- mpv (automatically installed with package managers)

## Development

```bash
# Clone the repo
git clone https://github.com/Umar-Khan-Yousafzai/Wrkmon-TUI-Youtube.git
cd Wrkmon-TUI-Youtube

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

**Umar Khan Yousafzai**

---

*Made with ❤️ for productive procrastinators everywhere*
