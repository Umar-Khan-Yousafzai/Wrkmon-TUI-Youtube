"""Search view container for wrkmon."""

import logging
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, Input, ListView
from textual.binding import Binding
from textual.events import Key
from textual import on

from wrkmon.core.youtube import SearchResult
from wrkmon.ui.messages import TrackSelected, TrackQueued, StatusMessage
from wrkmon.ui.widgets.result_item import ResultItem

logger = logging.getLogger("wrkmon.search")


class SearchView(Vertical):
    """Main search view - search YouTube and display results."""

    BINDINGS = [
        Binding("a", "queue_selected", "Add to Queue", show=True),
        Binding("escape", "clear_search", "Clear", show=True),
        Binding("/", "focus_search", "Search", show=True),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.results: list[SearchResult] = []
        self._is_searching = False

    def compose(self) -> ComposeResult:
        yield Static("SEARCH", id="view-title")

        with Vertical(id="search-container"):
            yield Input(
                placeholder="Search processes...",
                id="search-input",
            )

        yield Static(
            " #   Process                                   PID   Duration  Status",
            id="list-header",
        )

        yield ListView(id="results-list")
        yield Static("Type to search", id="status-bar")

    def on_mount(self) -> None:
        """Focus the search input on mount."""
        self.query_one("#search-input", Input).focus()

    @on(Input.Submitted, "#search-input")
    async def handle_search(self, event: Input.Submitted) -> None:
        """Execute search when Enter is pressed."""
        query = event.value.strip()
        if not query or self._is_searching:
            return

        self._is_searching = True
        self._update_status("Searching...")

        try:
            # Access the app's YouTube client
            youtube = self.app.youtube
            self.results = await youtube.search(query, max_results=15)
            self._display_results()
        except Exception as e:
            self._update_status(f"Search failed: {e}")
            self.post_message(StatusMessage(f"Search error: {e}", "error"))
        finally:
            self._is_searching = False

    def _display_results(self) -> None:
        """Display search results in the list."""
        list_view = self.query_one("#results-list", ListView)
        list_view.clear()

        if not self.results:
            self._update_status("No results found")
            return

        for i, result in enumerate(self.results, 1):
            list_view.append(ResultItem(result, i))

        self._update_status(f"Found {len(self.results)} | Enter=Play  A=Queue  /=Search  ↑↓=Nav")
        list_view.focus()

    def _update_status(self, message: str) -> None:
        """Update the status bar."""
        try:
            self.query_one("#status-bar", Static).update(message)
        except Exception:
            pass

    def _get_selected(self) -> SearchResult | None:
        """Get the currently selected result."""
        list_view = self.query_one("#results-list", ListView)
        if list_view.highlighted_child is None:
            return None

        item = list_view.highlighted_child
        if isinstance(item, ResultItem):
            return item.result
        return None

    def action_clear_search(self) -> None:
        """Clear the search input."""
        search_input = self.query_one("#search-input", Input)
        if search_input.value:
            search_input.value = ""
        search_input.focus()

    @on(ListView.Selected, "#results-list")
    def handle_result_selected(self, event: ListView.Selected) -> None:
        """Handle Enter key on a result - play it."""
        if isinstance(event.item, ResultItem):
            result = event.item.result
            self.post_message(TrackSelected(result))
            self._update_status(f"Playing: {result.title[:40]}...")

    def action_queue_selected(self) -> None:
        """Add selected track to queue."""
        logger.info("=== 'a' PRESSED: action_queue_selected ===")
        result = self._get_selected()
        logger.info(f"  Selected result: {result}")
        if result:
            logger.info(f"  Posting TrackQueued for: {result.title}")
            self.post_message(TrackQueued(result))
            self._update_status(f"Queued: {result.title[:40]}...")
        else:
            logger.warning("  No result selected!")

    def focus_input(self) -> None:
        """Focus the search input (called from parent)."""
        self.query_one("#search-input", Input).focus()

    def action_focus_search(self) -> None:
        """Focus the search input (/ key)."""
        self.focus_input()

    def on_key(self, event: Key) -> None:
        """Handle key events - up at top of list goes to search."""
        if event.key == "up":
            list_view = self.query_one("#results-list", ListView)
            # If list is focused and at top (index 0), go to search input
            if list_view.has_focus and list_view.index == 0:
                self.focus_input()
                event.prevent_default()
                event.stop()
