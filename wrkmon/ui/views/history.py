"""History view container for wrkmon."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, ListView
from textual.binding import Binding
from textual import on

from wrkmon.core.youtube import SearchResult
from wrkmon.data.models import HistoryEntry
from wrkmon.ui.widgets.result_item import HistoryItem
from wrkmon.ui.messages import TrackSelected, TrackQueued, StatusMessage


class HistoryView(Vertical):
    """History view - shows recently played tracks."""

    BINDINGS = [
        Binding("a", "queue_selected", "Add to Queue", show=True),
        Binding("c", "clear_history", "Clear All", show=True),
        Binding("r", "refresh", "Refresh", show=True),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.entries: list[HistoryEntry] = []

    def compose(self) -> ComposeResult:
        yield Static("HISTORY", id="view-title")

        yield Static(
            " #   Process                              Duration  Runs  Last Run",
            id="list-header",
        )

        yield ListView(id="history-list")
        yield Static("Loading history...", id="status-bar")

    def on_mount(self) -> None:
        """Load history on mount."""
        self.load_history()

    def load_history(self) -> None:
        """Load play history from database."""
        try:
            db = self.app.database
            self.entries = db.get_history(limit=100)
            self._display_history()
        except Exception as e:
            self._update_status(f"Failed to load history: {e}")

    def _display_history(self) -> None:
        """Display history entries."""
        list_view = self.query_one("#history-list", ListView)
        list_view.clear()

        if not self.entries:
            self._update_status("No history yet")
            return

        for i, entry in enumerate(self.entries, 1):
            track = entry.track
            last_played = entry.played_at.strftime("%m-%d %H:%M")

            list_view.append(
                HistoryItem(
                    title=track.title,
                    duration=track.duration,
                    play_count=entry.play_count,
                    last_played=last_played,
                    index=i,
                    video_id=track.video_id,
                    channel=track.channel,
                )
            )

        total_plays = sum(e.play_count for e in self.entries)
        self._update_status(f"{len(self.entries)} tracks, {total_plays} total plays")

    def _update_status(self, message: str) -> None:
        """Update status bar."""
        try:
            self.query_one("#status-bar", Static).update(message)
        except Exception:
            pass

    def _get_selected(self) -> HistoryItem | None:
        """Get the currently selected history item."""
        list_view = self.query_one("#history-list", ListView)
        if list_view.highlighted_child is None:
            return None

        item = list_view.highlighted_child
        if isinstance(item, HistoryItem):
            return item
        return None

    def _item_to_result(self, item: HistoryItem) -> SearchResult:
        """Convert a history item to a SearchResult."""
        return SearchResult(
            video_id=item.video_id,
            title=item.title,
            channel=item.channel,
            duration=item.duration,
            view_count=0,
        )

    @on(ListView.Selected, "#history-list")
    def handle_item_selected(self, event: ListView.Selected) -> None:
        """Handle Enter key on a history item - play it."""
        if isinstance(event.item, HistoryItem):
            result = self._item_to_result(event.item)
            self.post_message(TrackSelected(result))
            self._update_status(f"Playing: {event.item.title[:40]}...")

    def action_queue_selected(self) -> None:
        """Add selected track to queue."""
        item = self._get_selected()
        if item:
            result = self._item_to_result(item)
            self.post_message(TrackQueued(result))
            self._update_status(f"Queued: {item.title[:40]}...")

    def action_clear_history(self) -> None:
        """Clear all history."""
        try:
            db = self.app.database
            count = db.clear_history()
            self.entries = []
            self._display_history()
            self.post_message(StatusMessage(f"Cleared {count} entries", "info"))
        except Exception as e:
            self.post_message(StatusMessage(f"Error: {e}", "error"))

    def action_refresh(self) -> None:
        """Refresh history."""
        self.load_history()
        self.post_message(StatusMessage("History refreshed", "info"))
