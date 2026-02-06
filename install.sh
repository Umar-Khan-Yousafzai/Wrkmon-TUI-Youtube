#!/usr/bin/env bash
# wrkmon installer - Cross-platform installation script
# Usage: curl -sSL https://raw.githubusercontent.com/Umar-Khan-Yousafzai/Wrkmon-TUI-Youtube/main/install.sh | bash
#   or:  wget -qO- https://raw.githubusercontent.com/Umar-Khan-Yousafzai/Wrkmon-TUI-Youtube/main/install.sh | bash

set -euo pipefail

VERSION="1.3.1"

# Colors (safe for non-color terminals)
if [ -t 1 ] && command -v tput >/dev/null 2>&1; then
    RED=$(tput setaf 1 2>/dev/null || echo "")
    GREEN=$(tput setaf 2 2>/dev/null || echo "")
    YELLOW=$(tput setaf 3 2>/dev/null || echo "")
    CYAN=$(tput setaf 6 2>/dev/null || echo "")
    BOLD=$(tput bold 2>/dev/null || echo "")
    RESET=$(tput sgr0 2>/dev/null || echo "")
else
    RED="" GREEN="" YELLOW="" CYAN="" BOLD="" RESET=""
fi

info()  { echo "${CYAN}[INFO]${RESET}  $*"; }
ok()    { echo "${GREEN}[OK]${RESET}    $*"; }
warn()  { echo "${YELLOW}[WARN]${RESET}  $*"; }
err()   { echo "${RED}[ERROR]${RESET} $*" >&2; }
die()   { err "$@"; exit 1; }

# ---------------------------------------------------------------------------
# OS Detection using uname (more reliable than $OSTYPE)
# ---------------------------------------------------------------------------
detect_os() {
    local kernel
    kernel="$(uname -s 2>/dev/null || echo "unknown")"

    case "$kernel" in
        Linux*)
            # Check for WSL
            if grep -qiE '(microsoft|wsl)' /proc/version 2>/dev/null; then
                OS="wsl"
            else
                OS="linux"
            fi
            ;;
        Darwin*)
            OS="macos"
            ;;
        CYGWIN*|MINGW*|MSYS*|MINGW32*|MINGW64*)
            OS="windows"
            ;;
        FreeBSD*)
            OS="freebsd"
            ;;
        *)
            # Fallback to $OSTYPE if uname didn't help
            case "${OSTYPE:-}" in
                linux*)   OS="linux" ;;
                darwin*)  OS="macos" ;;
                msys*|cygwin*|win32*) OS="windows" ;;
                freebsd*) OS="freebsd" ;;
                *)        OS="unknown" ;;
            esac
            ;;
    esac

    # Detect architecture
    ARCH="$(uname -m 2>/dev/null || echo "x86_64")"
}

# ---------------------------------------------------------------------------
# Package manager detection (Linux)
# ---------------------------------------------------------------------------
detect_linux_pkg_manager() {
    if command -v apt-get >/dev/null 2>&1; then
        PKG_MGR="apt"
    elif command -v dnf >/dev/null 2>&1; then
        PKG_MGR="dnf"
    elif command -v pacman >/dev/null 2>&1; then
        PKG_MGR="pacman"
    elif command -v zypper >/dev/null 2>&1; then
        PKG_MGR="zypper"
    elif command -v apk >/dev/null 2>&1; then
        PKG_MGR="apk"
    elif command -v emerge >/dev/null 2>&1; then
        PKG_MGR="portage"
    elif command -v xbps-install >/dev/null 2>&1; then
        PKG_MGR="xbps"
    elif command -v nix-env >/dev/null 2>&1; then
        PKG_MGR="nix"
    else
        PKG_MGR=""
    fi
}

# Determine sudo command (might not be available)
get_sudo() {
    if [ "$(id -u)" -eq 0 ]; then
        SUDO=""
    elif command -v sudo >/dev/null 2>&1; then
        SUDO="sudo"
    elif command -v doas >/dev/null 2>&1; then
        SUDO="doas"
    else
        SUDO=""
        warn "Neither sudo nor doas found. Installation may require root."
    fi
}

# ---------------------------------------------------------------------------
# Python check
# ---------------------------------------------------------------------------
check_python() {
    info "Checking Python installation..."

    PYTHON=""
    for cmd in python3 python; do
        if command -v "$cmd" >/dev/null 2>&1; then
            local ver
            ver="$("$cmd" -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || echo "0")"
            local major
            major="$("$cmd" -c 'import sys; print(sys.version_info.major)' 2>/dev/null || echo "0")"
            if [ "$major" -eq 3 ] && [ "$ver" -ge 10 ]; then
                PYTHON="$cmd"
                break
            fi
        fi
    done

    if [ -z "$PYTHON" ]; then
        err "Python 3.10+ is required but not found."
        echo ""
        case "$OS" in
            linux|wsl)
                echo "  Install with your package manager:"
                echo "    ${CYAN}sudo apt install python3${RESET}    (Debian/Ubuntu)"
                echo "    ${CYAN}sudo dnf install python3${RESET}    (Fedora/RHEL)"
                echo "    ${CYAN}sudo pacman -S python${RESET}       (Arch)"
                ;;
            macos)
                echo "  Install with Homebrew:"
                echo "    ${CYAN}brew install python@3.12${RESET}"
                echo "  Or download from: https://python.org"
                ;;
            freebsd)
                echo "  Install with pkg:"
                echo "    ${CYAN}sudo pkg install python3${RESET}"
                ;;
            windows)
                echo "  Install with:"
                echo "    ${CYAN}winget install Python.Python.3.12${RESET}"
                ;;
        esac
        die "Please install Python 3.10+ and re-run this script."
    fi

    local full_ver
    full_ver="$("$PYTHON" --version 2>&1)"
    ok "Found: $full_ver"
}

# ---------------------------------------------------------------------------
# pip check
# ---------------------------------------------------------------------------
check_pip() {
    if ! "$PYTHON" -m pip --version >/dev/null 2>&1; then
        warn "pip not found, attempting to install..."
        case "$OS" in
            linux|wsl)
                if [ "$PKG_MGR" = "apt" ]; then
                    $SUDO apt-get install -y python3-pip 2>/dev/null || true
                fi
                ;;
        esac
        # Try ensurepip as fallback
        "$PYTHON" -m ensurepip --upgrade 2>/dev/null || true

        if ! "$PYTHON" -m pip --version >/dev/null 2>&1; then
            die "pip is not available. Install it: ${CYAN}$PYTHON -m ensurepip --upgrade${RESET}"
        fi
    fi
    ok "pip is available"
}

# ---------------------------------------------------------------------------
# mpv installation
# ---------------------------------------------------------------------------
install_mpv() {
    info "Checking mpv installation..."

    if command -v mpv >/dev/null 2>&1; then
        ok "mpv is already installed: $(mpv --version 2>/dev/null | head -1 || echo 'unknown version')"
        return 0
    fi

    info "Installing mpv..."
    get_sudo

    case "$OS" in
        linux|wsl)
            detect_linux_pkg_manager
            case "$PKG_MGR" in
                apt)     $SUDO apt-get update -qq && $SUDO apt-get install -y mpv ;;
                dnf)     $SUDO dnf install -y mpv ;;
                pacman)  $SUDO pacman -S --noconfirm mpv ;;
                zypper)  $SUDO zypper install -y mpv ;;
                apk)     $SUDO apk add mpv ;;
                portage) $SUDO emerge --ask=n media-video/mpv ;;
                xbps)    $SUDO xbps-install -y mpv ;;
                nix)     nix-env -iA nixpkgs.mpv ;;
                *)
                    err "Could not detect package manager."
                    echo "  Please install mpv manually and re-run this script."
                    echo "  https://mpv.io/installation/"
                    return 1
                    ;;
            esac
            ;;
        macos)
            if command -v brew >/dev/null 2>&1; then
                brew install mpv
            elif command -v port >/dev/null 2>&1; then
                $SUDO port install mpv
            else
                err "No package manager found. Please install Homebrew first:"
                echo "  ${CYAN}/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"${RESET}"
                echo "  Then re-run this script."
                return 1
            fi
            ;;
        freebsd)
            $SUDO pkg install -y mpv
            ;;
        windows)
            if command -v winget >/dev/null 2>&1; then
                winget install mpv --silent --accept-package-agreements 2>/dev/null || true
            elif command -v choco >/dev/null 2>&1; then
                choco install mpv -y
            elif command -v scoop >/dev/null 2>&1; then
                scoop install mpv
            else
                err "No Windows package manager found."
                echo "  Install mpv with one of:"
                echo "    ${CYAN}winget install mpv${RESET}"
                echo "    ${CYAN}choco install mpv${RESET}"
                echo "    ${CYAN}scoop install mpv${RESET}"
                echo "  Or download from: https://mpv.io/installation/"
                return 1
            fi
            ;;
        *)
            err "Unsupported OS for automatic mpv installation."
            echo "  Please install mpv manually: https://mpv.io/installation/"
            return 1
            ;;
    esac

    # Verify installation
    if command -v mpv >/dev/null 2>&1; then
        ok "mpv installed successfully"
    else
        warn "mpv may have been installed but is not in PATH yet."
        warn "You may need to restart your terminal or add mpv to your PATH."
    fi
}

# ---------------------------------------------------------------------------
# deno installation (optional)
# ---------------------------------------------------------------------------
install_deno() {
    info "Checking JavaScript runtime (optional, for better YouTube support)..."

    if command -v deno >/dev/null 2>&1; then
        ok "deno is already installed"
        return 0
    fi

    if command -v node >/dev/null 2>&1; then
        ok "Node.js found - JavaScript runtime available (deno not needed)"
        return 0
    fi

    info "Installing deno (for better YouTube compatibility)..."

    case "$OS" in
        linux|wsl|freebsd)
            if curl -fsSL https://deno.land/install.sh 2>/dev/null | sh 2>/dev/null; then
                ok "deno installed"
                # Add to PATH for this session
                export DENO_INSTALL="${DENO_INSTALL:-$HOME/.deno}"
                export PATH="$DENO_INSTALL/bin:$PATH"
            else
                warn "Could not install deno automatically (this is optional)."
                echo "  Install manually: ${CYAN}curl -fsSL https://deno.land/install.sh | sh${RESET}"
            fi
            ;;
        macos)
            if command -v brew >/dev/null 2>&1; then
                brew install deno 2>/dev/null && ok "deno installed via Homebrew" || true
            else
                curl -fsSL https://deno.land/install.sh 2>/dev/null | sh 2>/dev/null && ok "deno installed" || true
            fi
            ;;
        windows)
            if command -v winget >/dev/null 2>&1; then
                winget install DenoLand.Deno --silent 2>/dev/null && ok "deno installed" || true
            elif command -v scoop >/dev/null 2>&1; then
                scoop install deno 2>/dev/null && ok "deno installed" || true
            elif command -v choco >/dev/null 2>&1; then
                choco install deno -y 2>/dev/null && ok "deno installed" || true
            else
                warn "Could not install deno automatically (this is optional)."
            fi
            ;;
        *)
            warn "Skipping deno installation on unsupported OS."
            ;;
    esac
}

# ---------------------------------------------------------------------------
# wrkmon installation
# ---------------------------------------------------------------------------
install_wrkmon() {
    info "Installing wrkmon..."

    "$PYTHON" -m pip install --upgrade pip 2>/dev/null || true
    "$PYTHON" -m pip install --upgrade wrkmon

    # Verify installation
    if "$PYTHON" -m wrkmon --version >/dev/null 2>&1 || command -v wrkmon >/dev/null 2>&1; then
        ok "wrkmon installed successfully!"
    else
        warn "wrkmon installed but 'wrkmon' command may not be in PATH."
        echo "  Try: ${CYAN}$PYTHON -m wrkmon${RESET}"
        echo "  Or add pip's bin directory to your PATH."
    fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    echo ""
    echo "${BOLD}${CYAN}==================================${RESET}"
    echo "${BOLD}${CYAN}  wrkmon Installer v${VERSION}${RESET}"
    echo "${BOLD}${CYAN}==================================${RESET}"
    echo ""

    detect_os
    info "Detected OS: ${BOLD}$OS${RESET} (arch: $ARCH)"

    if [ "$OS" = "unknown" ]; then
        warn "Could not detect your OS. The script will try its best."
    fi

    # For native Windows (not Git Bash), recommend the PowerShell installer
    if [ "$OS" = "windows" ]; then
        warn "For best results on Windows, use the PowerShell installer:"
        echo "  ${CYAN}irm https://raw.githubusercontent.com/Umar-Khan-Yousafzai/Wrkmon-TUI-Youtube/main/install.ps1 | iex${RESET}"
        echo ""
        echo "Continuing with bash installer anyway..."
        echo ""
    fi

    echo ""
    echo "${BOLD}Step 1: Checking Python...${RESET}"
    check_python
    check_pip

    echo ""
    echo "${BOLD}Step 2: Installing mpv (required)...${RESET}"
    install_mpv

    echo ""
    echo "${BOLD}Step 3: Installing deno (optional)...${RESET}"
    install_deno

    echo ""
    echo "${BOLD}Step 4: Installing wrkmon...${RESET}"
    install_wrkmon

    echo ""
    echo "${BOLD}${GREEN}==================================${RESET}"
    echo "${BOLD}${GREEN}  Installation Complete!${RESET}"
    echo "${BOLD}${GREEN}==================================${RESET}"
    echo ""
    echo "Run ${CYAN}wrkmon${RESET} to start the player."
    echo ""
    echo "${BOLD}Quick start:${RESET}"
    echo "  ${CYAN}wrkmon${RESET}          Launch TUI player"
    echo "  ${CYAN}wrkmon update${RESET}   Check for updates"
    echo "  ${CYAN}wrkmon deps${RESET}     Check dependencies"
    echo ""
    echo "${BOLD}Key controls:${RESET}"
    echo "  F1-F4  : Switch views (Search, Queue, History, Playlists)"
    echo "  F5     : Play/Pause      b : Focus mode"
    echo "  F9     : Stop            l : Lyrics"
    echo "  F10    : Add to queue    ? : Help"
    echo ""
}

main "$@"
