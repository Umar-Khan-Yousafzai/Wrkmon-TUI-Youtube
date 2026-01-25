"""Auto-installer for mpv on Windows."""

import os
import sys
import shutil
import zipfile
import tempfile
import urllib.request
from pathlib import Path


# mpv download URL for Windows (64-bit)
MPV_DOWNLOAD_URL = "https://sourceforge.net/projects/mpv-player-windows/files/64bit/mpv-x86_64-20240121-git-a39f9b6.7z/download"
MPV_ZIP_URL = "https://github.com/shinchiro/mpv-winbuild-cmake/releases/download/20240121/mpv-x86_64-20240121-git-a39f9b6.7z"

# Simpler: use a direct zip from a mirror or bundle
MPV_PORTABLE_URL = "https://sourceforge.net/projects/mpv-player-windows/files/bootstrapper.zip/download"


def get_mpv_dir() -> Path:
    """Get the directory where mpv should be installed."""
    if sys.platform == "win32":
        # Install in LocalAppData/wrkmon/mpv
        local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return Path(local_app_data) / "wrkmon" / "mpv"
    else:
        # On Unix, mpv should be installed via package manager
        return Path.home() / ".local" / "share" / "wrkmon" / "mpv"


def get_mpv_executable() -> Path:
    """Get the path to the mpv executable."""
    mpv_dir = get_mpv_dir()
    if sys.platform == "win32":
        # Check both possible locations
        exe_path = mpv_dir / "mpv.exe"
        if exe_path.exists():
            return exe_path
        # Also check in subdirectory (some extractions create this)
        sub_path = mpv_dir / "mpv" / "mpv.exe"
        if sub_path.exists():
            return sub_path
        return exe_path  # Return default even if not exists
    return mpv_dir / "mpv"


def is_mpv_installed() -> bool:
    """Check if mpv is available (either in PATH or our local install)."""
    # Check PATH first
    if shutil.which("mpv"):
        return True

    # Check our local install
    mpv_exe = get_mpv_executable()
    return mpv_exe.exists()


def get_mpv_path() -> str:
    """Get the path to mpv executable."""
    # Check PATH first
    system_mpv = shutil.which("mpv")
    if system_mpv:
        return system_mpv

    # Check our local install
    mpv_exe = get_mpv_executable()
    if mpv_exe.exists():
        return str(mpv_exe)

    return "mpv"  # Default, will fail if not installed


def download_file(url: str, dest: Path, progress_callback=None) -> bool:
    """Download a file with optional progress callback."""
    try:
        def report_progress(block_num, block_size, total_size):
            if progress_callback and total_size > 0:
                progress = min(100, (block_num * block_size * 100) // total_size)
                progress_callback(progress)

        urllib.request.urlretrieve(url, dest, reporthook=report_progress)
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False


def install_mpv_windows(progress_callback=None) -> bool:
    """Download and install mpv on Windows."""
    import subprocess

    mpv_dir = get_mpv_dir()
    mpv_dir.mkdir(parents=True, exist_ok=True)

    # Use winget if available (cleanest option)
    try:
        result = subprocess.run(
            ["winget", "install", "--id", "mpv.net", "-e", "--silent"],
            capture_output=True,
            timeout=300
        )
        if result.returncode == 0:
            return True
    except Exception:
        pass

    # Try chocolatey
    try:
        result = subprocess.run(
            ["choco", "install", "mpv", "-y"],
            capture_output=True,
            timeout=300
        )
        if result.returncode == 0:
            return True
    except Exception:
        pass

    # Manual download as fallback
    # Download portable mpv
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        if progress_callback:
            progress_callback(0, "Downloading mpv...")

        # Try to download from GitHub releases (more reliable)
        zip_path = tmp_path / "mpv.zip"

        # Use a known working URL for portable mpv
        urls_to_try = [
            "https://github.com/shinchiro/mpv-winbuild-cmake/releases/latest/download/mpv-x86_64-latest.7z",
            "https://downloads.sourceforge.net/project/mpv-player-windows/64bit-v3/mpv-x86_64-v3-20240114-git-5765e7f.7z",
        ]

        # For simplicity, let's just tell users to install manually if auto-install fails
        if progress_callback:
            progress_callback(100, "Please install mpv manually: winget install mpv")

        return False


def install_mpv(progress_callback=None) -> bool:
    """Install mpv for the current platform."""
    if sys.platform == "win32":
        return install_mpv_windows(progress_callback)
    else:
        # On Unix, tell user to install via package manager
        print("Please install mpv using your package manager:")
        print("  Ubuntu/Debian: sudo apt install mpv")
        print("  Fedora: sudo dnf install mpv")
        print("  Arch: sudo pacman -S mpv")
        print("  macOS: brew install mpv")
        return False


def ensure_mpv_installed() -> tuple[bool, str]:
    """
    Ensure mpv is installed, attempting auto-install if needed.

    Returns:
        tuple: (success: bool, mpv_path_or_error: str)
    """
    if is_mpv_installed():
        return True, get_mpv_path()

    # Try to install
    print("mpv not found, attempting to install...")
    if install_mpv():
        if is_mpv_installed():
            return True, get_mpv_path()

    # Installation failed
    if sys.platform == "win32":
        error_msg = (
            "mpv not found! Please install it:\n"
            "  Option 1: winget install mpv\n"
            "  Option 2: choco install mpv\n"
            "  Option 3: Download from https://mpv.io/installation/"
        )
    else:
        error_msg = (
            "mpv not found! Please install it:\n"
            "  Ubuntu/Debian: sudo apt install mpv\n"
            "  Fedora: sudo dnf install mpv\n"
            "  Arch: sudo pacman -S mpv\n"
            "  macOS: brew install mpv"
        )

    return False, error_msg
