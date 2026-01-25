"""History screen for wrkmon."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical
from textual.widgets import Static, ListView, ListItem, Label
from textual.binding import Binding

from wrkmon.data.models import HistoryEntry


class HistoryListItem(ListItem):
    """A history list item."""

    def __init__(self, entry: HistoryEntry, index: int, **kwargs):
        super().__init__(**kwargs)
        self.entry = entry
        self.index = index

    def compose(self) -> ComposeResult:
        from wrkmon.utils.stealth import get_stealth
        stealth = get_stealth()

        track = self.entry.track
        process_name = stealth.get_fake_process_name(track.title)[:35]
        duration = track.duration_str
        plays = self.entry.play_count
        played_at = self.entry.played_at.strftime("%Y-%m-%d %H:%M")

        text = f"{self.index:2}  {process_name:<37} {duration:>8}  {plays:>3}x  {played_at}"
        yield Label(text)


class HistoryScreen(Screen):
    """Play history screen."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=False),
        Binding("enter", "play_selected", "Play", show=False),
        Binding("q", "add_to_queue", "Add to Queue", show=False),
        Binding("c", "clear_history", "Clear History", show=False),
        Binding("r", "refresh", "Refresh", show=False),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.entries: list[HistoryEntry] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="history-screen"):
            yield Static("PROCESS HISTORY", id="history-header")
            yield Static(
                " #   Process Name                               Duration  Runs  Last Run",
                id="history-list-header",
            )
            yield ListView(id="history-list")
            yield Static("", id="history-status")

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.load_history()

    def load_history(self) -> None:
        """Load play history."""
        db = self.app.database
        self.entries = db.get_history(limit=100)
        self.display_history()

    def display_history(self) -> None:
        """Display history list."""
        list_view = self.query_one("#history-list", ListView)
        list_view.clear()

        if not self.entries:
            self.update_status("No history yet")
            return

        for i, entry in enumerate(self.entries, 1):
            list_view.append(HistoryListItem(entry, i))

        total_plays = sum(e.play_count for e in self.entries)
        self.update_status(f"{len(self.entries)} tracks, {total_plays} total plays")

    def update_status(self, message: str) -> None:
        """Update status message."""
        self.query_one("#history-status", Static).update(message)

    def action_go_back(self) -> None:
        """Go back."""
        self.app.pop_screen()

    async def action_play_selected(self) -> None:
        """Play the selected track."""
        list_view = self.query_one("#history-list", ListView)
        if list_view.highlighted_child is None:
            return

        item = list_view.highlighted_child
        if isinstance(item, HistoryListItem):
            track = item.entry.track
            from wrkmon.core.youtube import SearchResult
            result = SearchResult(
                video_id=track.video_id,
                title=track.title,
                channel=track.channel,
                duration=track.duration,
                view_count=0,
            )
            await self.app.play_track(result)

    def action_add_to_queue(self) -> None:
        """Add selected to queue."""
        list_view = self.query_one("#history-list", ListView)
        if list_view.highlighted_child is None:
            return

        item = list_view.highlighted_child
        if isinstance(item, HistoryListItem):
            track = item.entry.track
            from wrkmon.core.youtube import SearchResult
            result = SearchResult(
                video_id=track.video_id,
                title=track.title,
                channel=track.channel,
                duration=track.duration,
                view_count=0,
            )
            self.app.add_to_queue(result)
            self.update_status(f"Added to queue: {track.title[:30]}...")

    def action_clear_history(self) -> None:
        """Clear all history."""
        db = self.app.database
        count = db.clear_history()
        self.entries = []
        self.display_history()
        self.update_status(f"Cleared {count} history entries")

    def action_refresh(self) -> None:
        """Refresh history."""
        self.load_history()
        self.update_status("History refreshed")
