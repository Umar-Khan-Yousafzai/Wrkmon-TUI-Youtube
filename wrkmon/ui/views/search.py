"""Search view container for wrkmon."""

import asyncio
import logging
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Input, ListView, ListItem, Label
from textual.binding import Binding
from textual.events import Key
from textual import on

from wrkmon.core.youtube import SearchResult
from wrkmon.ui.messages import TrackSelected, TrackQueued, StatusMessage
from wrkmon.ui.widgets.result_item import ResultItem
from wrkmon.ui.widgets.thumbnail import ThumbnailPreview
from wrkmon.utils.config import get_config

logger = logging.getLogger("wrkmon.search")


class LoadMoreItem(ListItem):
    """Special list item for loading more results."""

    def __init__(self) -> None:
        super().__init__()
        self.is_load_more = True

    def compose(self):
        yield Label("  >>> Load More Results <<<", classes="load-more")


class SearchView(Vertical):
    """Main search view - search YouTube and display results."""

    BINDINGS = [
        Binding("a", "queue_selected", "Add to Queue", show=True),
        Binding("escape", "clear_search", "Clear", show=True),
        Binding("/", "focus_search", "Search", show=True),
        Binding("space", "play_selected", "Play", show=False, priority=True),
        Binding("r", "toggle_repeat", "Repeat", show=True),
        Binding("t", "toggle_thumbnail", "Thumb", show=True),
        Binding("y", "cycle_thumbnail_style", "Style", show=True),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.results: list[SearchResult] = []
        self._is_searching = False
        self._current_query = ""
        self._load_more_offset = 0
        self._batch_size = 15
        self._thumbnail_task: asyncio.Task | None = None
        self._is_trending = False  # True when showing trending, False after search

        # Load settings from config
        self._config = get_config()
        self._show_thumbnail = self._config.show_thumbnails
        self._thumbnail_style = self._config.thumbnail_style
        self._thumbnail_width = self._config.thumbnail_width

    def compose(self) -> ComposeResult:
        yield Static("TRENDING", id="view-title")

        with Vertical(id="search-container"):
            yield Input(
                placeholder="Search YouTube music...",
                id="search-input",
            )

        yield Static(
            " #   Title                                     Channel         Duration  Views",
            id="list-header",
        )

        with Horizontal(id="search-content"):
            yield ListView(id="results-list")
            with Vertical(id="thumbnail-panel"):
                yield Static("PREVIEW", id="thumb-title")
                yield ThumbnailPreview(
                    width=self._thumbnail_width,
                    style=self._thumbnail_style,
                    id="thumb-preview"
                )

        yield Static("Loading trending music...", id="status-bar")

    def on_mount(self) -> None:
        """Load trending videos and setup initial state on mount."""
        # Apply initial thumbnail visibility
        if not self._show_thumbnail:
            try:
                self.query_one("#thumbnail-panel", Vertical).add_class("hidden")
            except Exception:
                pass

        # Load trending videos if enabled
        if self._config.show_trending_on_start:
            asyncio.create_task(self._load_trending())
        else:
            self.query_one("#search-input", Input).focus()
            self._update_status("Type to search YouTube music")

    async def _load_trending(self) -> None:
        """Load trending/popular music videos on startup."""
        self._is_searching = True
        self._is_trending = True
        self._update_status("Loading trending music...")

        try:
            # Update view title to show trending
            self.query_one("#view-title", Static).update("TRENDING")

            # Access the app's YouTube client
            youtube = self.app.youtube
            self.results = await youtube.get_trending_music(max_results=15)

            if self.results:
                self._display_results(show_load_more=False)
                self._update_status(f"Trending: {len(self.results)} popular tracks | Search to find more")
            else:
                self._update_status("Could not load trending | Type to search")

        except Exception as e:
            logger.debug(f"Failed to load trending: {e}")
            self._update_status("Type to search YouTube music")
        finally:
            self._is_searching = False
            # Focus the list if we have results, otherwise search input
            if self.results:
                self.query_one("#results-list", ListView).focus()
            else:
                self.query_one("#search-input", Input).focus()

    @on(Input.Submitted, "#search-input")
    async def handle_search(self, event: Input.Submitted) -> None:
        """Execute search when Enter is pressed."""
        query = event.value.strip()
        if not query or self._is_searching:
            return

        self._is_searching = True
        self._is_trending = False  # No longer showing trending
        self._update_status("Searching...")
        self._current_query = query
        self._load_more_offset = 0

        # Update view title to SEARCH
        try:
            self.query_one("#view-title", Static).update("SEARCH")
        except Exception:
            pass

        try:
            # Access the app's YouTube client
            youtube = self.app.youtube
            self.results = await youtube.search(query, max_results=self._batch_size)
            self._display_results(show_load_more=True)
        except Exception as e:
            self._update_status(f"Search failed: {e}")
            self.post_message(StatusMessage(f"Search error: {e}", "error"))
        finally:
            self._is_searching = False

    async def _load_more_results(self) -> None:
        """Load more search results."""
        if not self._current_query or self._is_searching:
            return

        self._is_searching = True
        self._update_status("Loading more...")

        try:
            youtube = self.app.youtube
            self._load_more_offset += self._batch_size
            # Search with offset by fetching more and skipping existing
            new_results = await youtube.search(
                self._current_query,
                max_results=self._batch_size + self._load_more_offset
            )
            # Get only the new results we don't have yet
            if len(new_results) > len(self.results):
                self.results = new_results
                self._display_results(show_load_more=True)
            else:
                self._update_status(f"No more results | Found {len(self.results)} total")
        except Exception as e:
            self._update_status(f"Load more failed: {e}")
        finally:
            self._is_searching = False

    def _display_results(self, show_load_more: bool = False) -> None:
        """Display search results in the list."""
        list_view = self.query_one("#results-list", ListView)
        list_view.clear()

        if not self.results:
            self._update_status("No results found")
            return

        for i, result in enumerate(self.results, 1):
            list_view.append(ResultItem(result, i))

        # Add "Load More" option at the end
        if show_load_more:
            list_view.append(LoadMoreItem())

        # Build status with repeat indicator
        repeat_status = self._get_repeat_status()
        thumb_status = " [THUMB ON]" if self._show_thumbnail else ""
        status = f"Found {len(self.results)} | Enter=Play A=Queue R=Repeat T=Thumb{repeat_status}{thumb_status}"
        self._update_status(status)
        list_view.focus()

    def _get_repeat_status(self) -> str:
        """Get repeat mode status string."""
        try:
            mode = self.app.queue.repeat_mode
            if mode == "one":
                return " [R1]"
            elif mode == "all":
                return " [RA]"
        except Exception:
            pass
        return ""

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

    def _update_thumbnail_preview(self) -> None:
        """Update thumbnail preview for currently highlighted item."""
        if not self._show_thumbnail:
            return

        result = self._get_selected()
        if result:
            try:
                preview = self.query_one("#thumb-preview", ThumbnailPreview)
                title = self.query_one("#thumb-title", Static)
                title.update(result.title[:35] + "..." if len(result.title) > 35 else result.title)
                preview.set_video(result.video_id)
            except Exception:
                pass
        else:
            self._clear_thumbnail()

    def _clear_thumbnail(self) -> None:
        """Clear the thumbnail preview."""
        try:
            preview = self.query_one("#thumb-preview", ThumbnailPreview)
            title = self.query_one("#thumb-title", Static)
            title.update("PREVIEW")
            preview.clear()
        except Exception:
            pass

    @on(ListView.Highlighted, "#results-list")
    def handle_highlight_changed(self, event: ListView.Highlighted) -> None:
        """Update thumbnail when highlighted item changes."""
        self._update_thumbnail_preview()

    def action_toggle_thumbnail(self) -> None:
        """Toggle thumbnail preview visibility."""
        self._show_thumbnail = not self._show_thumbnail
        # Save to config
        self._config.show_thumbnails = self._show_thumbnail

        try:
            panel = self.query_one("#thumbnail-panel", Vertical)
            if self._show_thumbnail:
                panel.remove_class("hidden")
                self._update_thumbnail_preview()
            else:
                panel.add_class("hidden")

            # Update status
            repeat_status = self._get_repeat_status()
            thumb_status = " [THUMB ON]" if self._show_thumbnail else ""
            count = len(self.results) if self.results else 0
            self._update_status(f"Found {count} | T=Thumb{repeat_status}{thumb_status}")
        except Exception:
            pass

    def action_cycle_thumbnail_style(self) -> None:
        """Cycle through thumbnail rendering styles (Y key)."""
        styles = ["colored_blocks", "colored_simple", "braille", "blocks"]
        style_names = {
            "colored_blocks": "Color Blocks",
            "colored_simple": "Color Simple",
            "braille": "Braille",
            "blocks": "Grayscale",
        }

        try:
            current_idx = styles.index(self._thumbnail_style) if self._thumbnail_style in styles else 0
            next_idx = (current_idx + 1) % len(styles)
            self._thumbnail_style = styles[next_idx]

            # Save to config
            self._config.thumbnail_style = self._thumbnail_style

            # Update the preview widget
            preview = self.query_one("#thumb-preview", ThumbnailPreview)
            preview.set_style(self._thumbnail_style)

            # Update status to show new style
            self._update_status(f"Thumbnail style: {style_names[self._thumbnail_style]}")
        except Exception:
            pass

    def action_clear_search(self) -> None:
        """Clear the search input."""
        search_input = self.query_one("#search-input", Input)
        if search_input.value:
            search_input.value = ""
        self._clear_thumbnail()
        search_input.focus()

    @on(ListView.Selected, "#results-list")
    async def handle_result_selected(self, event: ListView.Selected) -> None:
        """Handle Enter key on a result - play it or load more."""
        if isinstance(event.item, LoadMoreItem):
            await self._load_more_results()
        elif isinstance(event.item, ResultItem):
            result = event.item.result
            self.post_message(TrackSelected(result))
            repeat_status = self._get_repeat_status()
            self._update_status(f"Playing: {result.title[:40]}...{repeat_status}")

    def action_play_selected(self) -> None:
        """Play the selected track (Space key)."""
        list_view = self.query_one("#results-list", ListView)
        if not list_view.has_focus:
            return
        result = self._get_selected()
        if result:
            self.post_message(TrackSelected(result))
            repeat_status = self._get_repeat_status()
            self._update_status(f"Playing: {result.title[:40]}...{repeat_status}")

    def action_toggle_repeat(self) -> None:
        """Cycle repeat mode (R key)."""
        try:
            mode = self.app.queue.cycle_repeat()
            mode_names = {"none": "OFF", "one": "ONE", "all": "ALL"}
            repeat_status = self._get_repeat_status()
            count = len(self.results) if self.results else 0
            thumb_status = " [THUMB ON]" if self._show_thumbnail else ""
            self._update_status(f"Repeat: {mode_names[mode]} | Found {count}{repeat_status}{thumb_status}")
        except Exception:
            pass

    def action_queue_selected(self) -> None:
        """Add selected track to queue."""
        logger.info("=== 'a' PRESSED: action_queue_selected ===")
        result = self._get_selected()
        logger.info(f"  Selected result: {result}")
        if result:
            logger.info(f"  Posting TrackQueued for: {result.title}")
            self.post_message(TrackQueued(result))
            repeat_status = self._get_repeat_status()
            self._update_status(f"Queued: {result.title[:40]}...{repeat_status}")
        else:
            logger.warning("  No result selected!")

    def focus_input(self) -> None:
        """Focus the search input (called from parent)."""
        self.query_one("#search-input", Input).focus()

    def action_focus_search(self) -> None:
        """Focus the search input (/ key)."""
        self.focus_input()

    def on_key(self, event: Key) -> None:
        """Handle key events - up at top of list goes to search, down from search goes to list."""
        if event.key == "up":
            list_view = self.query_one("#results-list", ListView)
            # If list is focused and at top (index 0), go to search input
            if list_view.has_focus and list_view.index == 0:
                self.focus_input()
                event.prevent_default()
                event.stop()
        elif event.key == "down":
            search_input = self.query_one("#search-input", Input)
            # If search input is focused, go to list
            if search_input.has_focus:
                list_view = self.query_one("#results-list", ListView)
                if len(list_view.children) > 0:
                    list_view.focus()
                    list_view.index = 0
                    event.prevent_default()
                    event.stop()

    def focus_list(self) -> None:
        """Focus the results list (called from parent)."""
        list_view = self.query_one("#results-list", ListView)
        if len(list_view.children) > 0:
            list_view.focus()
        else:
            self.query_one("#search-input", Input).focus()
