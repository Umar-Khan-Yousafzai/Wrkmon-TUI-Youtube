"""Audio player using mpv with IPC for proper control."""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from typing import Optional

from wrkmon.utils.config import get_config

logger = logging.getLogger("wrkmon.player")


class AudioPlayer:
    """mpv audio player with IPC for pause/resume/seek."""

    def __init__(self):
        self._config = get_config()
        self._process: Optional[subprocess.Popen] = None
        self._current_url: Optional[str] = None
        self._volume = 80
        self._paused = False
        self._position = 0.0
        self._duration = 0.0
        self._pipe_path = r"\\.\pipe\wrkmon_mpv" if sys.platform == "win32" else "/tmp/wrkmon_mpv.sock"
        self._pipe = None

    @property
    def is_connected(self) -> bool:
        return self._process is not None and self._process.poll() is None

    @property
    def is_playing(self) -> bool:
        return self.is_connected and not self._paused

    @property
    def current_position(self) -> float:
        return self._position

    @property
    def duration(self) -> float:
        return self._duration

    @property
    def volume(self) -> int:
        return self._volume

    async def start(self) -> bool:
        """Initialize player (no-op, starts on play)."""
        return True

    def _send_command(self, command: list) -> Optional[dict]:
        """Send command to mpv via IPC and get response."""
        if not self.is_connected:
            return None

        try:
            if sys.platform == "win32":
                import win32file
                import win32pipe

                # Open pipe
                handle = win32file.CreateFile(
                    self._pipe_path,
                    win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                    0, None,
                    win32file.OPEN_EXISTING,
                    0, None
                )

                # Send command
                cmd = json.dumps({"command": command}) + "\n"
                win32file.WriteFile(handle, cmd.encode())

                # Read response
                result, data = win32file.ReadFile(handle, 4096)
                win32file.CloseHandle(handle)

                if data:
                    return json.loads(data.decode().strip())
            else:
                # Unix socket
                import socket
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect(self._pipe_path)
                sock.settimeout(1.0)

                cmd = json.dumps({"command": command}) + "\n"
                sock.send(cmd.encode())

                data = sock.recv(4096)
                sock.close()

                if data:
                    return json.loads(data.decode().strip())

        except Exception as e:
            logger.debug(f"IPC command failed: {e}")

        return None

    async def _send_command_async(self, command: list) -> Optional[dict]:
        """Async wrapper for send_command."""
        return await asyncio.to_thread(self._send_command, command)

    async def play(self, url: str) -> bool:
        """Play audio from URL - stealth mode with IPC."""
        logger.info(f"=== player.play() called ===")
        logger.info(f"  URL: {url[:100]}...")

        # Kill any existing playback
        await self.stop()

        mpv_path = self._config.mpv_path
        logger.info(f"  mpv_path: {mpv_path}")

        # Check if mpv exists
        mpv_exists = os.path.exists(mpv_path) if mpv_path != "mpv" else True
        logger.info(f"  mpv exists: {mpv_exists}")

        # Args with IPC server for control
        args = [
            mpv_path,
            "--no-video",
            "--no-terminal",
            "--really-quiet",
            "--no-osc",
            "--no-osd-bar",
            "--force-window=no",
            "--audio-display=no",
            f"--volume={self._volume}",
            f"--input-ipc-server={self._pipe_path}",
            url,
        ]
        logger.info(f"  IPC pipe: {self._pipe_path}")

        try:
            if sys.platform == "win32":
                logger.info("  Creating Windows subprocess...")
                self._process = subprocess.Popen(
                    args,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            else:
                logger.info("  Creating Unix subprocess...")
                self._process = subprocess.Popen(
                    args,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )

            logger.info(f"  Process created, PID: {self._process.pid}")
            self._current_url = url
            self._paused = False

            # Wait for mpv to start and create pipe
            await asyncio.sleep(1.0)

            poll_result = self._process.poll()
            if poll_result is None:
                logger.info("  SUCCESS - mpv is running!")
                # Try to get duration
                await self._update_properties()
                return True
            else:
                logger.error(f"  FAILED - mpv exited with code: {poll_result}")
                return False

        except Exception as e:
            logger.exception(f"  EXCEPTION: {e}")
            return False

    async def _update_properties(self) -> None:
        """Update position and duration from mpv."""
        try:
            # Get time position
            result = await self._send_command_async(["get_property", "time-pos"])
            if result and "data" in result:
                self._position = float(result["data"] or 0)

            # Get duration
            result = await self._send_command_async(["get_property", "duration"])
            if result and "data" in result:
                self._duration = float(result["data"] or 0)

            # Get pause state
            result = await self._send_command_async(["get_property", "pause"])
            if result and "data" in result:
                self._paused = bool(result["data"])

        except Exception as e:
            logger.debug(f"Failed to update properties: {e}")

    async def stop(self) -> None:
        """Stop playback."""
        if self._process:
            try:
                # Try graceful quit first
                self._send_command(["quit"])
                await asyncio.sleep(0.2)
            except Exception:
                pass

            try:
                self._process.terminate()
                self._process.wait(timeout=2)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass
            self._process = None

        self._paused = False
        self._position = 0.0
        self._duration = 0.0

    async def pause(self) -> None:
        """Pause playback via IPC."""
        if self.is_connected:
            result = await self._send_command_async(["set_property", "pause", True])
            if result:
                self._paused = True
                logger.info("Paused via IPC")
            else:
                # Fallback - just set flag
                self._paused = True

    async def resume(self) -> None:
        """Resume playback via IPC."""
        if self.is_connected:
            result = await self._send_command_async(["set_property", "pause", False])
            if result:
                self._paused = False
                logger.info("Resumed via IPC")
            else:
                # Fallback - restart if IPC fails
                if self._current_url:
                    await self.play(self._current_url)
        self._paused = False

    async def toggle_pause(self) -> None:
        """Toggle pause state."""
        if self._paused:
            await self.resume()
        else:
            await self.pause()

    async def set_volume(self, volume: int) -> None:
        """Set volume."""
        self._volume = max(0, min(100, volume))
        if self.is_connected:
            await self._send_command_async(["set_property", "volume", self._volume])

    async def seek(self, seconds: float, relative: bool = True) -> None:
        """Seek in current track."""
        if self.is_connected:
            if relative:
                await self._send_command_async(["seek", seconds, "relative"])
            else:
                await self._send_command_async(["seek", seconds, "absolute"])

    async def get_position(self) -> float:
        """Get current playback position."""
        await self._update_properties()
        return self._position

    async def get_duration(self) -> float:
        """Get current track duration."""
        await self._update_properties()
        return self._duration

    async def shutdown(self) -> None:
        """Shutdown player."""
        await self.stop()

    def on_property_change(self, name: str, callback) -> None:
        """Register callback - not implemented yet."""
        pass

    async def get_property(self, name: str):
        """Get property."""
        if name == "volume":
            return self._volume
        if name == "pause":
            return self._paused
        if name == "time-pos":
            await self._update_properties()
            return self._position
        if name == "duration":
            await self._update_properties()
            return self._duration
        return None
