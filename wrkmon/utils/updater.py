"""Version checker and updater for wrkmon."""

import asyncio
import json
import logging
import shutil
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from packaging import version

from wrkmon import __version__

logger = logging.getLogger("wrkmon.updater")

PYPI_URL = "https://pypi.org/pypi/wrkmon/json"
CHECK_INTERVAL_HOURS = 24


@dataclass
class UpdateInfo:
    """Information about an available update."""

    current_version: str
    latest_version: str
    is_update_available: bool
    release_url: str = "https://pypi.org/project/wrkmon/"

    @property
    def update_command(self) -> str:
        """Get the command to update wrkmon."""
        return "pip install --upgrade wrkmon"


def get_current_version() -> str:
    """Get the current installed version."""
    return __version__


def check_pypi_version() -> Optional[str]:
    """
    Check PyPI for the latest version of wrkmon.

    Returns:
        The latest version string, or None if check failed.
    """
    try:
        req = urllib.request.Request(
            PYPI_URL,
            headers={"Accept": "application/json", "User-Agent": "wrkmon-updater"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data.get("info", {}).get("version")
    except Exception as e:
        logger.debug(f"Failed to check PyPI version: {e}")
        return None


async def check_pypi_version_async() -> Optional[str]:
    """Async wrapper for checking PyPI version."""
    return await asyncio.to_thread(check_pypi_version)


def compare_versions(current: str, latest: str) -> bool:
    """
    Check if an update is available.

    Returns:
        True if latest > current (update available).
    """
    try:
        return version.parse(latest) > version.parse(current)
    except Exception:
        # Fallback to string comparison
        return latest != current and latest > current


def check_for_updates() -> Optional[UpdateInfo]:
    """
    Check if a newer version is available on PyPI.

    Returns:
        UpdateInfo if check succeeded, None if check failed.
    """
    current = get_current_version()
    latest = check_pypi_version()

    if latest is None:
        return None

    return UpdateInfo(
        current_version=current,
        latest_version=latest,
        is_update_available=compare_versions(current, latest),
    )


async def check_for_updates_async() -> Optional[UpdateInfo]:
    """Async version of check_for_updates."""
    return await asyncio.to_thread(check_for_updates)


def perform_update() -> tuple[bool, str]:
    """
    Attempt to update wrkmon using pip.

    Returns:
        tuple: (success, message)
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "wrkmon"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            return True, "Update successful! Please restart wrkmon."
        else:
            return False, f"Update failed: {result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Update timed out. Try manually: pip install --upgrade wrkmon"
    except Exception as e:
        return False, f"Update error: {e}"


async def perform_update_async() -> tuple[bool, str]:
    """Async version of perform_update."""
    return await asyncio.to_thread(perform_update)


# ============================================================
# Dependency checkers for better compatibility
# ============================================================

def is_deno_installed() -> bool:
    """Check if deno is installed."""
    return shutil.which("deno") is not None


def is_nodejs_installed() -> bool:
    """Check if Node.js is installed."""
    return shutil.which("node") is not None


def get_js_runtime() -> Optional[str]:
    """Get the available JavaScript runtime for yt-dlp."""
    if is_deno_installed():
        return "deno"
    if is_nodejs_installed():
        return "nodejs"
    return None


def get_deno_install_command() -> str:
    """Get the command to install deno for the current platform."""
    if sys.platform == "win32":
        return "irm https://deno.land/install.ps1 | iex"
    else:
        return "curl -fsSL https://deno.land/install.sh | sh"


def install_deno() -> tuple[bool, str]:
    """
    Attempt to install deno.

    Returns:
        tuple: (success, message)
    """
    if is_deno_installed():
        return True, "deno is already installed"

    try:
        if sys.platform == "win32":
            # Try winget first
            try:
                result = subprocess.run(
                    ["winget", "install", "--id", "DenoLand.Deno", "-e", "--silent"],
                    capture_output=True,
                    timeout=300,
                )
                if result.returncode == 0:
                    return True, "deno installed via winget"
            except Exception:
                pass

            # Try scoop
            try:
                result = subprocess.run(
                    ["scoop", "install", "deno"],
                    capture_output=True,
                    timeout=300,
                )
                if result.returncode == 0:
                    return True, "deno installed via scoop"
            except Exception:
                pass

            # Try chocolatey
            try:
                result = subprocess.run(
                    ["choco", "install", "deno", "-y"],
                    capture_output=True,
                    timeout=300,
                )
                if result.returncode == 0:
                    return True, "deno installed via chocolatey"
            except Exception:
                pass

            return False, f"Please install deno manually:\n{get_deno_install_command()}"

        else:
            # Unix - try package managers first
            if sys.platform == "darwin":
                # macOS - try brew
                try:
                    result = subprocess.run(
                        ["brew", "install", "deno"],
                        capture_output=True,
                        timeout=300,
                    )
                    if result.returncode == 0:
                        return True, "deno installed via homebrew"
                except Exception:
                    pass
            else:
                # Linux - try snap
                try:
                    result = subprocess.run(
                        ["snap", "install", "deno"],
                        capture_output=True,
                        timeout=300,
                    )
                    if result.returncode == 0:
                        return True, "deno installed via snap"
                except Exception:
                    pass

            # Try the official install script
            try:
                result = subprocess.run(
                    ["sh", "-c", "curl -fsSL https://deno.land/install.sh | sh"],
                    capture_output=True,
                    timeout=300,
                )
                if result.returncode == 0:
                    return True, "deno installed via official script"
            except Exception:
                pass

            return False, f"Please install deno manually:\n{get_deno_install_command()}"

    except Exception as e:
        return False, f"Installation failed: {e}"


async def install_deno_async() -> tuple[bool, str]:
    """Async version of install_deno."""
    return await asyncio.to_thread(install_deno)


def check_dependencies() -> dict:
    """
    Check all optional dependencies for optimal functionality.

    Returns:
        dict with dependency status.
    """
    from wrkmon.utils.mpv_installer import is_mpv_installed

    return {
        "mpv": {
            "installed": is_mpv_installed(),
            "required": True,
            "description": "Media player for audio playback",
        },
        "deno": {
            "installed": is_deno_installed(),
            "required": False,
            "description": "JavaScript runtime for better YouTube compatibility",
        },
        "nodejs": {
            "installed": is_nodejs_installed(),
            "required": False,
            "description": "Alternative JavaScript runtime",
        },
        "js_runtime": {
            "installed": get_js_runtime() is not None,
            "required": False,
            "description": "JavaScript runtime (deno or nodejs) for full YouTube support",
        },
    }


def get_missing_dependencies() -> list[str]:
    """Get list of missing recommended dependencies."""
    deps = check_dependencies()
    missing = []

    if not deps["mpv"]["installed"]:
        missing.append("mpv")
    if not deps["js_runtime"]["installed"]:
        missing.append("deno (recommended for YouTube)")

    return missing
