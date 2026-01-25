"""Queue view container for wrkmon."""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, ListView, ProgressBar
from textual.binding import Binding
from textual.reactive import reactive

from wrkmon.ui.widgets.result_item import QueueItem
from wrkmon.ui.messages import StatusMessage
from wrkmon.utils.stealth import get_stealth


class QueueView(Vertical):
    """Queue/Player view - shows current playback and queue."""

    BINDINGS = [
        Binding("space", "toggle_pause", "Play/Pause", show=True),
        Binding("n", "next_track", "Next", show=True),
        Binding("p", "prev_track", "Previous", show=True),
        Binding("s", "toggle_shuffle", "Shuffle", show=True),
        Binding("r", "toggle_repeat", "Repeat", show=True),
        Binding("c", "clear_queue", "Clear Queue", show=True),
        Binding("delete", "remove_selected", "Remove", show=False),
    ]

    # Reactive state
    shuffle_enabled = reactive(False)
    repeat_mode = reactive("none")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._stealth = get_stealth()

    def compose(self) -> ComposeResult:
        yield Static("QUEUE", id="view-title")

        # Now playing section
        with Vertical(id="now-playing-section"):
            yield Static("NOW RUNNING", id="section-header")
            yield Static("No process running", id="current-track")

            with Horizontal(id="playback-progress"):
                yield Static("--:--", id="pos-time")
                yield ProgressBar(total=100, show_percentage=False, id="track-progress")
                yield Static("--:--", id="dur-time")

        # Mode indicators
        with Horizontal(id="mode-indicators"):
            yield Static("", id="shuffle-indicator")
            yield Static("", id="repeat-indicator")

        # Queue list
        yield Static(
            "   #   Process                                    Duration  Status",
            id="list-header",
        )
        yield ListView(id="queue-list")
        yield Static("Queue empty", id="status-bar")

    def on_mount(self) -> None:
        """Initialize the view."""
        self.refresh_queue()

    def refresh_queue(self) -> None:
        """Refresh the queue display."""
        try:
            queue = self.app.queue
            list_view = self.query_one("#queue-list", ListView)
            list_view.clear()

            items = queue.to_list()
            if not items:
                self._update_status("Queue empty")
                return

            for i, item in enumerate(items):
                is_current = i == queue.current_index
                list_view.append(
                    QueueItem(
                        title=item.title,
                        duration=item.duration,
                        index=i + 1,
                        is_current=is_current,
                    )
                )

            self._update_status(f"{len(items)} in queue")
            self._update_mode_indicators()
        except Exception:
            pass

    def update_now_playing(self, title: str, position: float, duration: float) -> None:
        """Update the now playing display."""
        try:
            process_name = self._stealth.get_fake_process_name(title)
            self.query_one("#current-track", Static).update(process_name)
            self.query_one("#pos-time", Static).update(self._stealth.format_duration(position))
            self.query_one("#dur-time", Static).update(self._stealth.format_duration(duration))

            if duration > 0:
                progress = (position / duration) * 100
                self.query_one("#track-progress", ProgressBar).update(progress=progress)
        except Exception:
            pass

    def _update_status(self, message: str) -> None:
        """Update status bar."""
        try:
            self.query_one("#status-bar", Static).update(message)
        except Exception:
            pass

    def _update_mode_indicators(self) -> None:
        """Update shuffle/repeat indicators."""
        try:
            queue = self.app.queue

            shuffle_text = "[SHUFFLE]" if queue.shuffle_mode else ""
            self.query_one("#shuffle-indicator", Static).update(shuffle_text)

            repeat_text = ""
            if queue.repeat_mode == "one":
                repeat_text = "[REPEAT ONE]"
            elif queue.repeat_mode == "all":
                repeat_text = "[REPEAT ALL]"
            self.query_one("#repeat-indicator", Static).update(repeat_text)
        except Exception:
            pass

    async def action_toggle_pause(self) -> None:
        """Toggle playback."""
        try:
            await self.app.toggle_pause()
        except Exception:
            pass

    async def action_next_track(self) -> None:
        """Play next track."""
        try:
            await self.app.play_next()
            self.refresh_queue()
        except Exception:
            pass

    async def action_prev_track(self) -> None:
        """Play previous track."""
        try:
            await self.app.play_previous()
            self.refresh_queue()
        except Exception:
            pass

    def action_toggle_shuffle(self) -> None:
        """Toggle shuffle mode."""
        try:
            is_shuffle = self.app.queue.toggle_shuffle()
            self._update_mode_indicators()
            status = "Shuffle ON" if is_shuffle else "Shuffle OFF"
            self.post_message(StatusMessage(status, "info"))
        except Exception:
            pass

    def action_toggle_repeat(self) -> None:
        """Cycle repeat mode."""
        try:
            mode = self.app.queue.cycle_repeat()
            self._update_mode_indicators()
            mode_names = {"none": "OFF", "one": "ONE", "all": "ALL"}
            self.post_message(StatusMessage(f"Repeat: {mode_names[mode]}", "info"))
        except Exception:
            pass

    def action_clear_queue(self) -> None:
        """Clear the queue."""
        try:
            self.app.queue.clear()
            self.refresh_queue()
            self.post_message(StatusMessage("Queue cleared", "info"))
        except Exception:
            pass

    def action_remove_selected(self) -> None:
        """Remove selected item from queue."""
        try:
            list_view = self.query_one("#queue-list", ListView)
            if list_view.index is not None:
                self.app.queue.remove(list_view.index)
                self.refresh_queue()
        except Exception:
            pass
