"""Cross-platform media key support for wrkmon.

Linux: Uses MPRIS D-Bus interface (standard way for desktop environments)
Windows/macOS: Uses pynput for global hotkey listening
"""

import asyncio
import logging
import sys
from typing import Callable, Optional, Any

logger = logging.getLogger("wrkmon.media_keys")

# Platform detection
IS_LINUX = sys.platform == "linux"
IS_WINDOWS = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"

# Check available backends
MPRIS_AVAILABLE = False
PYNPUT_AVAILABLE = False

if IS_LINUX:
    try:
        from dbus_next.aio import MessageBus
        from dbus_next.service import ServiceInterface, method, dbus_property
        from dbus_next import Variant, BusType
        MPRIS_AVAILABLE = True
    except ImportError:
        logger.debug("dbus-next not installed, MPRIS support disabled")

if IS_WINDOWS or IS_MACOS:
    try:
        from pynput import keyboard
        PYNPUT_AVAILABLE = True
    except ImportError:
        logger.debug("pynput not installed, global hotkey support disabled")


# ============================================
# MPRIS Implementation (Linux)
# ============================================

if MPRIS_AVAILABLE:
    class MPRISRootInterface(ServiceInterface):
        """MPRIS MediaPlayer2 root interface."""

        def __init__(self, callback: Callable):
            super().__init__("org.mpris.MediaPlayer2")
            self._callback = callback

        @method()
        def Raise(self):
            pass

        @method()
        def Quit(self):
            asyncio.create_task(self._callback("quit"))

        @dbus_property()
        def CanQuit(self) -> "b":
            return True

        @dbus_property()
        def CanRaise(self) -> "b":
            return False

        @dbus_property()
        def HasTrackList(self) -> "b":
            return False

        @dbus_property()
        def Identity(self) -> "s":
            return "wrkmon"

        @dbus_property()
        def DesktopEntry(self) -> "s":
            return "wrkmon"

        @dbus_property()
        def SupportedUriSchemes(self) -> "as":
            return ["https", "http"]

        @dbus_property()
        def SupportedMimeTypes(self) -> "as":
            return ["audio/mpeg", "audio/ogg", "audio/webm"]


    class MPRISPlayerInterface(ServiceInterface):
        """MPRIS MediaPlayer2.Player interface."""

        def __init__(self, callback: Callable):
            super().__init__("org.mpris.MediaPlayer2.Player")
            self._callback = callback
            self._is_playing = False
            self._position = 0
            self._metadata: dict = {}
            self._volume = 1.0

        @method()
        def Next(self):
            logger.info("MPRIS: Next track")
            asyncio.create_task(self._callback("next"))

        @method()
        def Previous(self):
            logger.info("MPRIS: Previous track")
            asyncio.create_task(self._callback("previous"))

        @method()
        def Pause(self):
            logger.info("MPRIS: Pause")
            asyncio.create_task(self._callback("pause"))

        @method()
        def PlayPause(self):
            logger.info("MPRIS: PlayPause")
            asyncio.create_task(self._callback("play_pause"))

        @method()
        def Stop(self):
            logger.info("MPRIS: Stop")
            asyncio.create_task(self._callback("stop"))

        @method()
        def Play(self):
            logger.info("MPRIS: Play")
            asyncio.create_task(self._callback("play"))

        @method()
        def Seek(self, offset: "x"):
            asyncio.create_task(self._callback("seek", offset / 1_000_000))

        @method()
        def SetPosition(self, track_id: "o", position: "x"):
            asyncio.create_task(self._callback("set_position", position / 1_000_000))

        @dbus_property()
        def PlaybackStatus(self) -> "s":
            return "Playing" if self._is_playing else "Paused"

        @dbus_property()
        def Rate(self) -> "d":
            return 1.0

        @dbus_property()
        def Metadata(self) -> "a{sv}":
            return self._metadata

        @dbus_property()
        def Volume(self) -> "d":
            return self._volume

        @Volume.setter
        def Volume(self, value: "d"):
            self._volume = max(0.0, min(1.0, value))
            asyncio.create_task(self._callback("set_volume", int(self._volume * 100)))

        @dbus_property()
        def Position(self) -> "x":
            return int(self._position * 1_000_000)

        @dbus_property()
        def MinimumRate(self) -> "d":
            return 1.0

        @dbus_property()
        def MaximumRate(self) -> "d":
            return 1.0

        @dbus_property()
        def CanGoNext(self) -> "b":
            return True

        @dbus_property()
        def CanGoPrevious(self) -> "b":
            return True

        @dbus_property()
        def CanPlay(self) -> "b":
            return True

        @dbus_property()
        def CanPause(self) -> "b":
            return True

        @dbus_property()
        def CanSeek(self) -> "b":
            return True

        @dbus_property()
        def CanControl(self) -> "b":
            return True

        def set_playing(self, playing: bool):
            self._is_playing = playing

        def set_position(self, pos: float):
            self._position = pos

        def set_volume(self, vol: int):
            self._volume = vol / 100.0

        def set_metadata(self, title: str, artist: str, duration: int, art_url: str, track_id: str):
            self._metadata = {
                "mpris:trackid": Variant("o", f"/org/mpris/MediaPlayer2/Track/{track_id or 'unknown'}"),
                "mpris:length": Variant("x", duration * 1_000_000),
                "xesam:title": Variant("s", title),
                "xesam:artist": Variant("as", [artist] if artist else []),
            }
            if art_url:
                self._metadata["mpris:artUrl"] = Variant("s", art_url)


# ============================================
# Cross-platform MediaKeysHandler
# ============================================

class MediaKeysHandler:
    """Cross-platform media keys handler."""

    def __init__(self, callback: Callable):
        """
        Initialize media keys handler.

        Args:
            callback: Async function called with (command, *args).
                     Commands: 'play', 'pause', 'play_pause', 'stop',
                              'next', 'previous', 'seek', 'set_volume', 'quit'
        """
        self._callback = callback
        self._running = False

        # Platform-specific components
        self._bus: Optional[Any] = None
        self._root_interface: Optional[Any] = None
        self._player_interface: Optional[Any] = None
        self._keyboard_listener: Optional[Any] = None

    @property
    def is_available(self) -> bool:
        """Check if media keys are available on this platform."""
        if IS_LINUX:
            return MPRIS_AVAILABLE
        return PYNPUT_AVAILABLE

    @property
    def is_running(self) -> bool:
        """Check if media keys handler is active."""
        return self._running

    @property
    def backend_name(self) -> str:
        """Get the name of the active backend."""
        if IS_LINUX and MPRIS_AVAILABLE:
            return "MPRIS (D-Bus)"
        elif PYNPUT_AVAILABLE:
            return "pynput (global hotkeys)"
        return "none"

    async def start(self) -> bool:
        """Start listening for media keys."""
        if self._running:
            return True

        if IS_LINUX:
            return await self._start_mpris()
        elif PYNPUT_AVAILABLE:
            return self._start_pynput()

        logger.info("No media key backend available")
        return False

    async def stop(self):
        """Stop listening for media keys."""
        if IS_LINUX and self._bus:
            try:
                self._bus.disconnect()
            except Exception:
                pass

        if self._keyboard_listener:
            try:
                self._keyboard_listener.stop()
            except Exception:
                pass

        self._running = False
        logger.info("Media keys handler stopped")

    async def _start_mpris(self) -> bool:
        """Start MPRIS D-Bus service (Linux)."""
        if not MPRIS_AVAILABLE:
            return False

        try:
            self._bus = await MessageBus(bus_type=BusType.SESSION).connect()
            self._root_interface = MPRISRootInterface(self._callback)
            self._player_interface = MPRISPlayerInterface(self._callback)

            self._bus.export("/org/mpris/MediaPlayer2", self._root_interface)
            self._bus.export("/org/mpris/MediaPlayer2", self._player_interface)

            await self._bus.request_name("org.mpris.MediaPlayer2.wrkmon")

            self._running = True
            logger.info("MPRIS service started - media keys active")
            return True

        except Exception as e:
            logger.warning(f"Failed to start MPRIS: {e}")
            return False

    def _start_pynput(self) -> bool:
        """Start pynput global hotkey listener (Windows/macOS)."""
        if not PYNPUT_AVAILABLE:
            return False

        try:
            def on_press(key):
                try:
                    # Check for media keys
                    if hasattr(key, 'name'):
                        if key == keyboard.Key.media_play_pause:
                            asyncio.create_task(self._callback("play_pause"))
                        elif key == keyboard.Key.media_next:
                            asyncio.create_task(self._callback("next"))
                        elif key == keyboard.Key.media_previous:
                            asyncio.create_task(self._callback("previous"))
                        elif key == keyboard.Key.media_volume_up:
                            asyncio.create_task(self._callback("volume_up"))
                        elif key == keyboard.Key.media_volume_down:
                            asyncio.create_task(self._callback("volume_down"))
                        elif key == keyboard.Key.media_volume_mute:
                            asyncio.create_task(self._callback("mute"))
                except Exception as e:
                    logger.debug(f"Error handling key: {e}")

            self._keyboard_listener = keyboard.Listener(on_press=on_press)
            self._keyboard_listener.start()

            self._running = True
            logger.info("pynput listener started - media keys active")
            return True

        except Exception as e:
            logger.warning(f"Failed to start pynput listener: {e}")
            return False

    def update_playback(self, is_playing: bool = None, position: float = None, volume: int = None):
        """Update playback state (for MPRIS)."""
        if not self._player_interface:
            return
        if is_playing is not None:
            self._player_interface.set_playing(is_playing)
        if position is not None:
            self._player_interface.set_position(position)
        if volume is not None:
            self._player_interface.set_volume(volume)

    def update_track(self, title: str = "", artist: str = "", duration: int = 0,
                     art_url: str = "", track_id: str = ""):
        """Update current track metadata (for MPRIS)."""
        if self._player_interface:
            self._player_interface.set_metadata(title, artist, duration, art_url, track_id)


# Singleton instance
_handler: Optional[MediaKeysHandler] = None


def get_media_keys_handler(callback: Callable = None) -> Optional[MediaKeysHandler]:
    """Get or create the media keys handler."""
    global _handler
    if _handler is None and callback:
        _handler = MediaKeysHandler(callback)
    return _handler
