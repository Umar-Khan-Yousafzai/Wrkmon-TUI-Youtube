#!/bin/bash
# wrkmon installer - Cross-platform installation script
# Usage: curl -sSL https://raw.githubusercontent.com/Umar-Khan-Yousafzai/Wrkmon-TUI-Youtube/main/install.sh | bash

set -e

echo "=================================="
echo "  wrkmon Installer"
echo "=================================="
echo ""

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    OS="windows"
fi

echo "Detected OS: $OS"
echo ""

# Install mpv if not present
install_mpv() {
    if command -v mpv &> /dev/null; then
        echo "mpv is already installed."
        return
    fi

    echo "Installing mpv..."

    case $OS in
        linux)
            if command -v apt &> /dev/null; then
                sudo apt update && sudo apt install -y mpv
            elif command -v dnf &> /dev/null; then
                sudo dnf install -y mpv
            elif command -v pacman &> /dev/null; then
                sudo pacman -S --noconfirm mpv
            elif command -v zypper &> /dev/null; then
                sudo zypper install -y mpv
            else
                echo "Could not detect package manager. Please install mpv manually."
                exit 1
            fi
            ;;
        macos)
            if command -v brew &> /dev/null; then
                brew install mpv
            else
                echo "Homebrew not found. Please install Homebrew first:"
                echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
                exit 1
            fi
            ;;
        windows)
            if command -v choco &> /dev/null; then
                choco install mpv -y
            elif command -v winget &> /dev/null; then
                winget install mpv --silent
            else
                echo "Please install mpv manually:"
                echo "  winget install mpv"
                echo "  or: choco install mpv"
                exit 1
            fi
            ;;
    esac
}

# Install Python if not present
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON="python3"
    elif command -v python &> /dev/null; then
        PYTHON="python"
    else
        echo "Python 3.10+ is required but not found."
        echo "Please install Python from https://python.org"
        exit 1
    fi

    # Check version
    VERSION=$($PYTHON -c 'import sys; print(sys.version_info.minor)')
    if [ "$VERSION" -lt 10 ]; then
        echo "Python 3.10+ is required. Found: 3.$VERSION"
        exit 1
    fi

    echo "Python found: $($PYTHON --version)"
}

# Install wrkmon
install_wrkmon() {
    echo ""
    echo "Installing wrkmon..."
    $PYTHON -m pip install --upgrade pip
    $PYTHON -m pip install wrkmon
}

# Main
echo "Step 1: Checking Python..."
check_python

echo ""
echo "Step 2: Installing mpv..."
install_mpv

echo ""
echo "Step 3: Installing wrkmon..."
install_wrkmon

echo ""
echo "=================================="
echo "  Installation Complete!"
echo "=================================="
echo ""
echo "Run 'wrkmon' to start the player."
echo ""
echo "Controls:"
echo "  F1-F4  : Switch views (Search, Queue, History, Playlists)"
echo "  F5     : Play/Pause"
echo "  F9     : Stop"
echo "  F10    : Add to queue"
echo "  /      : Focus search"
echo ""
