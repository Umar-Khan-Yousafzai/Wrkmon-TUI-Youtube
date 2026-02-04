"""ASCII thumbnail widget for wrkmon - with color support."""

import asyncio
from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import Static

from wrkmon.utils.ascii_art import get_or_fetch_ascii, get_cached_ascii, clear_cache


class ThumbnailPreview(Static):
    """Widget to display colored ASCII art thumbnail preview."""

    DEFAULT_CSS = """
    ThumbnailPreview {
        width: 100%;
        height: auto;
        min-height: 8;
        max-height: 18;
        background: #0d1117;
        padding: 0;
    }

    ThumbnailPreview.loading {
        color: #6e7681;
    }

    ThumbnailPreview.hidden {
        display: none;
    }
    """

    video_id = reactive("")
    is_loading = reactive(False)
    style_mode = reactive("colored_blocks")  # colored_blocks, colored_simple, blocks, braille

    def __init__(
        self,
        video_id: str = "",
        width: int = 45,
        style: str = "colored_blocks",
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self._ascii_width = width
        self._current_task: asyncio.Task | None = None
        self.style_mode = style
        if video_id:
            self.video_id = video_id

    def compose(self) -> ComposeResult:
        yield Static("", id="ascii-content", markup=True)

    def on_mount(self) -> None:
        """Load thumbnail on mount if video_id is set."""
        if self.video_id:
            self._load_thumbnail()

    def watch_video_id(self, video_id: str) -> None:
        """React to video_id changes."""
        if video_id:
            self._load_thumbnail()
        else:
            self._clear_thumbnail()

    def _load_thumbnail(self) -> None:
        """Load ASCII thumbnail for current video."""
        if not self.video_id:
            return

        # Check cache first
        cache_key = f"{self.video_id}_{self.style_mode}_{self._ascii_width}"
        from wrkmon.utils.ascii_art import _thumbnail_cache
        cached = _thumbnail_cache.get(cache_key)
        if cached:
            self._display_ascii(cached)
            return

        # Load async
        self.is_loading = True
        self.add_class("loading")
        self._update_content("[dim]Loading...[/]")

        # Cancel any existing task
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()

        # Start new load task
        self._current_task = asyncio.create_task(self._fetch_and_display())

    async def _fetch_and_display(self) -> None:
        """Fetch thumbnail and display it."""
        try:
            ascii_art = await get_or_fetch_ascii(
                self.video_id,
                width=self._ascii_width,
                style=self.style_mode,
            )

            if ascii_art:
                self._display_ascii(ascii_art)
            else:
                self._update_content("[dim]No thumbnail[/]")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self._update_content(f"[red]Error: {e}[/]")
        finally:
            self.is_loading = False
            self.remove_class("loading")

    def _display_ascii(self, ascii_art: str) -> None:
        """Display ASCII art in the widget."""
        self._update_content(ascii_art)

    def _update_content(self, content: str) -> None:
        """Update the content display."""
        try:
            widget = self.query_one("#ascii-content", Static)
            widget.update(content)
        except Exception:
            pass

    def _clear_thumbnail(self) -> None:
        """Clear the thumbnail display."""
        self._update_content("")

    def set_video(self, video_id: str) -> None:
        """Set video ID and load thumbnail."""
        self.video_id = video_id

    def set_style(self, style: str) -> None:
        """Change the rendering style and reload."""
        if style != self.style_mode:
            self.style_mode = style
            if self.video_id:
                self._load_thumbnail()

    def clear(self) -> None:
        """Clear the thumbnail."""
        self.video_id = ""

    def show(self) -> None:
        """Show the widget."""
        self.remove_class("hidden")

    def hide(self) -> None:
        """Hide the widget."""
        self.add_class("hidden")

    def cycle_style(self) -> str:
        """Cycle through rendering styles."""
        styles = ["colored_blocks", "colored_simple", "braille", "blocks"]
        current_idx = styles.index(self.style_mode) if self.style_mode in styles else 0
        next_idx = (current_idx + 1) % len(styles)
        self.set_style(styles[next_idx])
        return styles[next_idx]


class ThumbnailPanel(Container):
    """Panel containing thumbnail preview with title."""

    DEFAULT_CSS = """
    ThumbnailPanel {
        width: 100%;
        height: auto;
        background: #161b22;
        border: solid #30363d;
        padding: 1;
    }

    ThumbnailPanel > #panel-title {
        height: 1;
        color: #58a6ff;
        text-style: bold;
        margin-bottom: 1;
    }

    ThumbnailPanel.hidden {
        display: none;
    }
    """

    def __init__(self, title: str = "Preview", width: int = 45, **kwargs) -> None:
        super().__init__(**kwargs)
        self._title = title
        self._width = width

    def compose(self) -> ComposeResult:
        yield Static(self._title, id="panel-title", markup=True)
        yield ThumbnailPreview(width=self._width, id="thumbnail-preview")

    def set_video(self, video_id: str, title: str = "") -> None:
        """Set video to preview."""
        if title:
            try:
                display_title = title[:40] + "..." if len(title) > 40 else title
                self.query_one("#panel-title", Static).update(f"[bold]{display_title}[/]")
            except Exception:
                pass

        try:
            self.query_one("#thumbnail-preview", ThumbnailPreview).set_video(video_id)
        except Exception:
            pass

    def clear(self) -> None:
        """Clear the preview."""
        try:
            self.query_one("#thumbnail-preview", ThumbnailPreview).clear()
            self.query_one("#panel-title", Static).update("Preview")
        except Exception:
            pass

    def cycle_style(self) -> str:
        """Cycle the thumbnail style."""
        try:
            return self.query_one("#thumbnail-preview", ThumbnailPreview).cycle_style()
        except Exception:
            return "colored_blocks"

    def show(self) -> None:
        """Show the panel."""
        self.remove_class("hidden")

    def hide(self) -> None:
        """Hide the panel."""
        self.add_class("hidden")
