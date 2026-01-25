"""Search screen for wrkmon."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, ScrollableContainer
from textual.widgets import Static, Input, ListView, ListItem, Label
from textual.binding import Binding
from textual import on

from wrkmon.core.youtube import SearchResult


class SearchResultItem(ListItem):
    """A search result list item."""

    def __init__(self, result: SearchResult, index: int, **kwargs):
        super().__init__(**kwargs)
        self.result = result
        self.index = index

    def compose(self) -> ComposeResult:
        from wrkmon.utils.stealth import get_stealth
        stealth = get_stealth()

        process_name = stealth.get_fake_process_name(self.result.title)[:40]
        fake_pid = stealth.get_fake_pid()
        status = "READY"

        # Format: index | process name | pid | status
        text = f"{self.index:2}  {process_name:<42} {fake_pid:>6}  {status}"
        yield Label(text)


class SearchScreen(Screen):
    """Main search screen."""

    BINDINGS = [
        Binding("escape", "clear_or_back", "Clear/Back", show=False),
        Binding("/", "focus_search", "Search", show=False),
        Binding("enter", "play_selected", "Play", show=False),
        Binding("q", "add_to_queue", "Add to Queue", show=False),
        Binding("a", "add_to_playlist", "Add to Playlist", show=False),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.results: list[SearchResult] = []
        self._searching = False

    def compose(self) -> ComposeResult:
        with Vertical(id="search-screen"):
            # Search header
            yield Static("> Search: ", id="search-label")
            yield Input(placeholder="Enter search query...", id="search-input")

            # Results header (looks like ps output)
            yield Static(
                " #   Process Name                                  PID     Status",
                id="results-header",
            )

            # Results list
            yield ListView(id="results-list")

            # Status message
            yield Static("", id="status-message")

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.query_one("#search-input", Input).focus()

    @on(Input.Submitted, "#search-input")
    async def handle_search(self, event: Input.Submitted) -> None:
        """Handle search submission."""
        query = event.value.strip()
        if not query:
            return

        self._searching = True
        self.update_status("Searching...")

        try:
            youtube = self.app.youtube
            self.results = await youtube.search(query, max_results=15)
            self.display_results()
        except Exception as e:
            self.update_status(f"Search failed: {e}")
        finally:
            self._searching = False

    def display_results(self) -> None:
        """Display search results."""
        list_view = self.query_one("#results-list", ListView)
        list_view.clear()

        if not self.results:
            self.update_status("No results found")
            return

        for i, result in enumerate(self.results, 1):
            list_view.append(SearchResultItem(result, i))

        self.update_status(f"Found {len(self.results)} processes")
        list_view.focus()

    def update_status(self, message: str) -> None:
        """Update status message."""
        self.query_one("#status-message", Static).update(message)

    def action_focus_search(self) -> None:
        """Focus the search input."""
        self.query_one("#search-input", Input).focus()

    def action_clear_or_back(self) -> None:
        """Clear search or go back."""
        search_input = self.query_one("#search-input", Input)
        if search_input.value:
            search_input.value = ""
            search_input.focus()
        else:
            # Could go back to previous screen if we had one
            pass

    async def action_play_selected(self) -> None:
        """Play the selected result."""
        list_view = self.query_one("#results-list", ListView)
        if list_view.highlighted_child is None:
            return

        item = list_view.highlighted_child
        if isinstance(item, SearchResultItem):
            await self.app.play_track(item.result)

    async def action_add_to_queue(self) -> None:
        """Add selected to queue."""
        list_view = self.query_one("#results-list", ListView)
        if list_view.highlighted_child is None:
            return

        item = list_view.highlighted_child
        if isinstance(item, SearchResultItem):
            self.app.add_to_queue(item.result)
            self.update_status(f"Added to queue: {item.result.title[:30]}...")

    def action_add_to_playlist(self) -> None:
        """Add selected to a playlist."""
        list_view = self.query_one("#results-list", ListView)
        if list_view.highlighted_child is None:
            return

        item = list_view.highlighted_child
        if isinstance(item, SearchResultItem):
            # TODO: Show playlist selection modal
            self.update_status("Playlist feature coming soon")

    def get_selected_result(self) -> SearchResult | None:
        """Get the currently selected search result."""
        list_view = self.query_one("#results-list", ListView)
        if list_view.highlighted_child is None:
            return None

        item = list_view.highlighted_child
        if isinstance(item, SearchResultItem):
            return item.result
        return None
