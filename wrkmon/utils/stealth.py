"""Stealth utilities for wrkmon - makes everything look like a dev tool."""

import os
import sys
import random
from typing import Optional


class StealthManager:
    """Manages stealth features for the application."""

    # Fake process names that look like legitimate dev tools
    FAKE_PROCESS_NAMES = [
        "node-inspector",
        "webpack-dev-srv",
        "vite-hmr-watch",
        "eslint-daemon",
        "tsc-watch",
        "pytest-runner",
        "cargo-watch",
        "go-build-srv",
        "rust-analyzer",
        "prettier-fmt",
    ]

    # Fake CPU/Memory stats ranges for the UI
    CPU_RANGE = (12, 45)
    MEM_RANGE = (35, 65)

    def __init__(self):
        self._original_title: Optional[str] = None

    def get_pipe_name(self) -> str:
        """Get the IPC pipe/socket name for mpv."""
        if sys.platform == "win32":
            return r"\\.\pipe\wrkmon-mpv"
        else:
            # Unix socket in runtime dir
            runtime_dir = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
            return f"{runtime_dir}/wrkmon-mpv.sock"

    def get_fake_process_name(self, video_title: str) -> str:
        """Convert a video title to a fake process name."""
        # Sanitize and truncate the title
        name = video_title.lower()
        # Replace spaces and special chars with hyphens
        name = "".join(c if c.isalnum() else "-" for c in name)
        # Remove consecutive hyphens
        while "--" in name:
            name = name.replace("--", "-")
        # Trim and limit length
        name = name.strip("-")[:30]
        return name or "media-process"

    def get_fake_pid(self) -> int:
        """Generate a fake PID that looks realistic."""
        return random.randint(1000, 65535)

    def get_fake_cpu(self) -> int:
        """Get a fake CPU usage percentage."""
        return random.randint(*self.CPU_RANGE)

    def get_fake_memory(self) -> int:
        """Get a fake memory usage percentage."""
        return random.randint(*self.MEM_RANGE)

    def set_terminal_title(self, title: str = "wrkmon") -> None:
        """Set the terminal window title."""
        if sys.platform == "win32":
            os.system(f"title {title}")
        else:
            # ANSI escape sequence for setting terminal title
            sys.stdout.write(f"\033]0;{title}\007")
            sys.stdout.flush()

    def restore_terminal_title(self) -> None:
        """Restore the original terminal title."""
        if self._original_title:
            self.set_terminal_title(self._original_title)

    def get_mpv_args(self) -> list[str]:
        """Get mpv arguments for stealth operation."""
        return [
            "--no-video",
            "--no-terminal",
            "--really-quiet",
            f"--input-ipc-server={self.get_pipe_name()}",
            "--idle=yes",
            "--force-window=no",
        ]

    def format_status(self, status: str) -> str:
        """Format a status string to look like a system status."""
        status_map = {
            "playing": "RUNNING",
            "paused": "SUSPENDED",
            "stopped": "STOPPED",
            "buffering": "LOADING",
            "ready": "READY",
            "error": "FAILED",
        }
        return status_map.get(status.lower(), status.upper())

    def format_duration(self, seconds: float) -> str:
        """Format duration in a clean way."""
        if seconds < 0:
            return "--:--"
        mins, secs = divmod(int(seconds), 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            return f"{hours}:{mins:02d}:{secs:02d}"
        return f"{mins}:{secs:02d}"


# Global stealth manager instance
_stealth: Optional[StealthManager] = None


def get_stealth() -> StealthManager:
    """Get the global stealth manager instance."""
    global _stealth
    if _stealth is None:
        _stealth = StealthManager()
    return _stealth
