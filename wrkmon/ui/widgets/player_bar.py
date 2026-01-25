"""Player bar widget - persistent playback controls at the bottom."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Static, ProgressBar

from wrkmon.utils.stealth import get_stealth


class PlayerBar(Static):
    """Persistent player bar showing current track and playback controls."""

    # Reactive state
    title = reactive("No process running")
    is_playing = reactive(False)
    position = reactive(0.0)
    duration = reactive(0.0)
    volume = reactive(80)
    status_text = reactive("")  # For showing errors/buffering

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._stealth = get_stealth()

    def compose(self) -> ComposeResult:
        with Vertical(id="player-bar-inner"):
            # Now playing row
            with Horizontal(id="now-playing-row"):
                yield Static("NOW", id="now-label", classes="label")
                yield Static(self._get_status_icon(), id="play-status")
                yield Static(self.title, id="track-title")

            # Progress row
            with Horizontal(id="progress-row"):
                yield Static(self._format_time(0), id="time-current")
                yield ProgressBar(total=100, show_percentage=False, id="progress")
                yield Static(self._format_time(0), id="time-total")

            # Volume row
            with Horizontal(id="volume-row"):
                yield Static("VOL", id="vol-label", classes="label")
                yield ProgressBar(total=100, show_percentage=False, id="volume")
                yield Static(f"{self.volume}%", id="vol-value")

    def _get_status_icon(self) -> str:
        return "▶" if self.is_playing else "■"

    def _format_time(self, seconds: float) -> str:
        return self._stealth.format_duration(seconds)

    def _format_title(self, title: str) -> str:
        return self._stealth.get_fake_process_name(title)

    # Watchers for reactive properties
    def watch_title(self, new_title: str) -> None:
        """Update title display."""
        try:
            display_title = self._format_title(new_title) if new_title else "No process running"
            self.query_one("#track-title", Static).update(display_title)
        except Exception:
            pass

    def watch_is_playing(self) -> None:
        """Update play/pause icon."""
        try:
            self.query_one("#play-status", Static).update(self._get_status_icon())
        except Exception:
            pass

    def watch_position(self, new_pos: float) -> None:
        """Update progress bar and time."""
        try:
            self.query_one("#time-current", Static).update(self._format_time(new_pos))
            if self.duration > 0:
                progress = (new_pos / self.duration) * 100
                self.query_one("#progress", ProgressBar).update(progress=progress)
        except Exception:
            pass

    def watch_duration(self, new_dur: float) -> None:
        """Update total duration display."""
        try:
            self.query_one("#time-total", Static).update(self._format_time(new_dur))
        except Exception:
            pass

    def watch_volume(self, new_vol: int) -> None:
        """Update volume display."""
        try:
            self.query_one("#volume", ProgressBar).update(progress=new_vol)
            self.query_one("#vol-value", Static).update(f"{new_vol}%")
        except Exception:
            pass

    def update_playback(
        self,
        title: str | None = None,
        is_playing: bool | None = None,
        position: float | None = None,
        duration: float | None = None,
    ) -> None:
        """Batch update playback state."""
        if title is not None:
            self.title = title
        if is_playing is not None:
            self.is_playing = is_playing
        if position is not None:
            self.position = position
        if duration is not None:
            self.duration = duration

    def set_volume(self, volume: int) -> None:
        """Update volume display."""
        self.volume = max(0, min(100, volume))
