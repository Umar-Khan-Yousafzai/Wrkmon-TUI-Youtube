"""Player bar widget - persistent playback controls at the bottom."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.events import Click
from textual.reactive import reactive
from textual.widgets import Static, ProgressBar

from wrkmon.ui.messages import SeekRequested
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
    repeat_mode = reactive("none")  # none, one, all
    is_muted = reactive(False)

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
                yield Static("", id="repeat-indicator")

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
        """Get status icon with color markup."""
        if self.is_playing:
            return "[bold green]▶[/]"
        else:
            return "[bold orange1]⏸[/]"

    def _get_status_text(self) -> str:
        """Get status text for stopped state."""
        return "[dim]■[/]"

    def _format_time(self, seconds: float) -> str:
        return self._stealth.format_duration(seconds)

    def _format_title(self, title: str) -> str:
        return self._stealth.get_fake_process_name(title)

    # Watchers for reactive properties
    def watch_title(self, new_title: str) -> None:
        """Update title display."""
        try:
            display_title = self._format_title(new_title) if new_title else "No process running"
            title_widget = self.query_one("#track-title", Static)
            title_widget.update(display_title)
        except Exception:
            pass

    def watch_is_playing(self) -> None:
        """Update play/pause icon."""
        try:
            status_widget = self.query_one("#play-status", Static)
            status_widget.update(self._get_status_icon())

            # Update CSS classes for styling
            if self.is_playing:
                status_widget.remove_class("paused")
                status_widget.remove_class("stopped")
            else:
                status_widget.add_class("paused")
        except Exception:
            pass

    def watch_position(self, new_pos: float) -> None:
        """Update progress bar and time."""
        try:
            time_widget = self.query_one("#time-current", Static)
            time_widget.update(self._format_time(new_pos))

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
            vol_text = f"{new_vol}%" if not self.is_muted else "[red]MUTE[/]"
            self.query_one("#vol-value", Static).update(vol_text)
        except Exception:
            pass

    def watch_is_muted(self, is_muted: bool) -> None:
        """Update mute indicator."""
        try:
            vol_text = f"{self.volume}%" if not is_muted else "[red]MUTE[/]"
            self.query_one("#vol-value", Static).update(vol_text)
        except Exception:
            pass

    def watch_repeat_mode(self, new_mode: str) -> None:
        """Update repeat indicator."""
        try:
            indicator = ""
            if new_mode == "one":
                indicator = "[bold purple]⟳1[/]"
            elif new_mode == "all":
                indicator = "[bold purple]⟳∞[/]"
            self.query_one("#repeat-indicator", Static).update(indicator)
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

    def set_muted(self, muted: bool) -> None:
        """Update mute state."""
        self.is_muted = muted

    def on_click(self, event: Click) -> None:
        """Handle click on the progress bar to seek."""
        try:
            progress_bar = self.query_one("#progress", ProgressBar)
            # Check if the click is within the progress bar's region
            region = progress_bar.region
            if region.contains(event.screen_x, event.screen_y) and self.duration > 0:
                # Calculate the seek position based on click X relative to the bar
                relative_x = event.screen_x - region.x
                fraction = max(0.0, min(1.0, relative_x / region.width))
                seek_to = fraction * self.duration
                self.post_message(SeekRequested(position=seek_to))
        except Exception:
            pass
