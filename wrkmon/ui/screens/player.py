"""Player screen for wrkmon."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, ProgressBar, ListView, ListItem, Label
from textual.binding import Binding
from textual.reactive import reactive

from wrkmon.core.queue import QueueItem


class QueueListItem(ListItem):
    """A queue list item."""

    def __init__(self, item: QueueItem, index: int, is_current: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.queue_item = item
        self.index = index
        self.is_current = is_current

    def compose(self) -> ComposeResult:
        from wrkmon.utils.stealth import get_stealth
        stealth = get_stealth()

        process_name = stealth.get_fake_process_name(self.queue_item.title)[:40]
        duration = stealth.format_duration(self.queue_item.duration)
        status = "RUNNING" if self.is_current else "QUEUED"

        prefix = ">" if self.is_current else " "
        text = f"{prefix} {self.index:2}  {process_name:<42} {duration:>8}  {status}"
        yield Label(text)


class PlayerScreen(Screen):
    """Player/Now Playing screen showing current track and queue."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=False),
        Binding("space", "toggle_pause", "Play/Pause", show=False),
        Binding("+", "volume_up", "Volume Up", show=False),
        Binding("-", "volume_down", "Volume Down", show=False),
        Binding("n", "next_track", "Next", show=False),
        Binding("p", "prev_track", "Previous", show=False),
        Binding("s", "toggle_shuffle", "Shuffle", show=False),
        Binding("r", "toggle_repeat", "Repeat", show=False),
        Binding("c", "clear_queue", "Clear Queue", show=False),
    ]

    title = reactive("No process running")
    status = reactive("STOPPED")
    position = reactive(0.0)
    duration = reactive(0.0)
    volume = reactive(80)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        from wrkmon.utils.stealth import get_stealth
        self._stealth = get_stealth()

        with Vertical(id="player-screen"):
            # Now playing section
            yield Static("NOW RUNNING", id="now-playing-header")
            yield Static("", id="now-playing-title")

            # Progress
            with Horizontal(id="progress-section"):
                yield ProgressBar(total=100, show_percentage=False, id="progress-bar")
                yield Static("--:-- / --:--", id="progress-time")

            # Controls status
            with Horizontal(id="controls-section"):
                yield Static("VOL:", id="vol-label")
                yield ProgressBar(total=100, show_percentage=False, id="volume-bar")
                yield Static("80%", id="volume-value")
                yield Static("", id="shuffle-status")
                yield Static("", id="repeat-status")

            # Queue section
            yield Static("PROCESS QUEUE", id="queue-header")
            yield Static(
                " #   Process Name                                  Duration    Status",
                id="queue-list-header",
            )
            yield ListView(id="queue-list")

            # Status
            yield Static("", id="player-status")

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.update_display()

    def update_display(self) -> None:
        """Update the entire display."""
        self.update_now_playing()
        self.update_queue()
        self.update_controls()

    def update_now_playing(self) -> None:
        """Update now playing display."""
        player = self.app.player
        queue = self.app.queue

        current = queue.current
        if current:
            process_name = self._stealth.get_fake_process_name(current.title)
            title_widget = self.query_one("#now-playing-title", Static)
            title_widget.update(f"  {process_name}")

            # Update progress
            pos = player.current_position
            dur = player.duration or current.duration
            self.update_progress(pos, dur)
        else:
            self.query_one("#now-playing-title", Static).update("  No process running")

    def update_progress(self, position: float, duration: float) -> None:
        """Update progress bar and time."""
        self.position = position
        self.duration = duration

        progress_bar = self.query_one("#progress-bar", ProgressBar)
        if duration > 0:
            progress_bar.update(progress=(position / duration) * 100)
        else:
            progress_bar.update(progress=0)

        pos_str = self._stealth.format_duration(position)
        dur_str = self._stealth.format_duration(duration)
        self.query_one("#progress-time", Static).update(f"{pos_str} / {dur_str}")

    def update_volume(self, volume: int) -> None:
        """Update volume display."""
        self.volume = volume
        self.query_one("#volume-bar", ProgressBar).update(progress=volume)
        self.query_one("#volume-value", Static).update(f"{volume}%")

    def update_controls(self) -> None:
        """Update control status indicators."""
        queue = self.app.queue

        shuffle_text = "[SHUF]" if queue.shuffle_mode else ""
        self.query_one("#shuffle-status", Static).update(shuffle_text)

        repeat_text = ""
        if queue.repeat_mode == "one":
            repeat_text = "[REP1]"
        elif queue.repeat_mode == "all":
            repeat_text = "[REPA]"
        self.query_one("#repeat-status", Static).update(repeat_text)

    def update_queue(self) -> None:
        """Update queue list."""
        queue = self.app.queue
        list_view = self.query_one("#queue-list", ListView)
        list_view.clear()

        items = queue.to_list()
        for i, item in enumerate(items):
            is_current = i == queue.current_index
            list_view.append(QueueListItem(item, i + 1, is_current))

        if not items:
            self.query_one("#player-status", Static).update("Queue empty")

    def update_status(self, message: str) -> None:
        """Update status message."""
        self.query_one("#player-status", Static).update(message)

    def action_go_back(self) -> None:
        """Go back to search screen."""
        self.app.pop_screen()

    async def action_toggle_pause(self) -> None:
        """Toggle play/pause."""
        await self.app.toggle_pause()
        status = "RUNNING" if self.app.player.is_playing else "SUSPENDED"
        self.update_status(f"Status: {status}")

    async def action_volume_up(self) -> None:
        """Increase volume."""
        new_vol = min(100, self.volume + 5)
        await self.app.set_volume(new_vol)
        self.update_volume(new_vol)

    async def action_volume_down(self) -> None:
        """Decrease volume."""
        new_vol = max(0, self.volume - 5)
        await self.app.set_volume(new_vol)
        self.update_volume(new_vol)

    async def action_next_track(self) -> None:
        """Play next track."""
        await self.app.play_next()
        self.update_display()

    async def action_prev_track(self) -> None:
        """Play previous track."""
        await self.app.play_previous()
        self.update_display()

    def action_toggle_shuffle(self) -> None:
        """Toggle shuffle mode."""
        is_shuffle = self.app.queue.toggle_shuffle()
        self.update_controls()
        self.update_status(f"Shuffle: {'ON' if is_shuffle else 'OFF'}")

    def action_toggle_repeat(self) -> None:
        """Toggle repeat mode."""
        mode = self.app.queue.cycle_repeat()
        self.update_controls()
        mode_names = {"none": "OFF", "one": "ONE", "all": "ALL"}
        self.update_status(f"Repeat: {mode_names[mode]}")

    def action_clear_queue(self) -> None:
        """Clear the queue."""
        self.app.queue.clear()
        self.update_queue()
        self.update_status("Queue cleared")
