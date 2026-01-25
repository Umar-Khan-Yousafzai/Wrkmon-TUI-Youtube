"""Reusable TUI components for wrkmon."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Input, ProgressBar, Label
from textual.reactive import reactive

from wrkmon.utils.stealth import get_stealth


class HeaderBar(Static):
    """Header bar showing app name and fake system stats."""

    cpu = reactive(23)
    mem = reactive(45)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._stealth = get_stealth()

    def compose(self) -> ComposeResult:
        with Horizontal(id="header"):
            yield Static("WRKMON v1.0.0", id="header-title")
            yield Static(self._get_stats_text(), id="header-stats")

    def _get_stats_text(self) -> str:
        return f"[CPU: {self.cpu}%] [MEM: {self.mem}%]"

    def update_stats(self) -> None:
        """Update fake system stats."""
        self.cpu = self._stealth.get_fake_cpu()
        self.mem = self._stealth.get_fake_memory()
        stats = self.query_one("#header-stats", Static)
        stats.update(self._get_stats_text())


class SearchBar(Static):
    """Search input bar."""

    def compose(self) -> ComposeResult:
        with Horizontal(id="search-container"):
            yield Static("> Search: ", classes="search-label")
            yield Input(placeholder="Enter search query...", id="search-input")

    def focus_input(self) -> None:
        """Focus the search input."""
        self.query_one("#search-input", Input).focus()

    def clear_input(self) -> None:
        """Clear the search input."""
        self.query_one("#search-input", Input).value = ""

    @property
    def value(self) -> str:
        """Get current search value."""
        return self.query_one("#search-input", Input).value


class ResultsHeader(Static):
    """Header row for results list (styled like ps/top output)."""

    def compose(self) -> ComposeResult:
        with Horizontal(id="results-header"):
            yield Static("#", classes="result-index")
            yield Static("Process Name", classes="result-title")
            yield Static("PID", classes="result-pid")
            yield Static("Status", classes="result-status")


class ResultItem(Static):
    """A single result item styled like a process entry."""

    def __init__(
        self,
        index: int,
        title: str,
        video_id: str,
        status: str = "READY",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.index = index
        self.title = title
        self.video_id = video_id
        self.status = status
        self._stealth = get_stealth()

    def compose(self) -> ComposeResult:
        fake_pid = self._stealth.get_fake_pid()
        process_name = self._stealth.get_fake_process_name(self.title)

        with Horizontal(classes="result-item"):
            yield Static(f"{self.index}", classes="result-index")
            yield Static(process_name[:40], classes="result-title")
            yield Static(str(fake_pid), classes="result-pid")
            status_class = f"status-{self.status.lower()}"
            yield Static(self.status, classes=f"result-status {status_class}")


class PlayerBar(Static):
    """Bottom player bar showing current track and controls."""

    title = reactive("No process running")
    status = reactive("STOPPED")
    position = reactive(0.0)
    duration = reactive(0.0)
    volume = reactive(80)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._stealth = get_stealth()

    def compose(self) -> ComposeResult:
        with Vertical(id="player-bar"):
            # Now playing line
            with Horizontal(id="now-playing"):
                yield Static("NOW:", id="now-playing-label")
                yield Static(self.title, id="now-playing-title")
                yield Static(self._get_status_icon(), id="now-playing-status")

            # Progress bar
            with Horizontal(id="progress-container"):
                yield ProgressBar(total=100, show_percentage=False, id="progress-bar")
                yield Static(self._get_time_text(), id="progress-time")

            # Volume bar
            with Horizontal(id="volume-container"):
                yield Static("VOL:", id="volume-label")
                yield ProgressBar(total=100, show_percentage=False, id="volume-bar")
                yield Static(f"{self.volume}%", id="volume-value")

    def _get_status_icon(self) -> str:
        icons = {
            "playing": "▶",
            "paused": "⏸",
            "stopped": "⏹",
            "buffering": "⟳",
        }
        return icons.get(self.status.lower(), "⏹")

    def _get_time_text(self) -> str:
        pos = self._stealth.format_duration(self.position)
        dur = self._stealth.format_duration(self.duration)
        return f"{pos} / {dur}"

    def update_now_playing(self, title: str, status: str) -> None:
        """Update the now playing display."""
        self.title = title
        self.status = status
        process_name = self._stealth.get_fake_process_name(title)
        self.query_one("#now-playing-title", Static).update(f"{process_name}")
        self.query_one("#now-playing-status", Static).update(self._get_status_icon())

    def update_progress(self, position: float, duration: float) -> None:
        """Update the progress bar."""
        self.position = position
        self.duration = duration

        progress_bar = self.query_one("#progress-bar", ProgressBar)
        if duration > 0:
            progress_bar.update(progress=(position / duration) * 100)
        else:
            progress_bar.update(progress=0)

        self.query_one("#progress-time", Static).update(self._get_time_text())

    def update_volume(self, volume: int) -> None:
        """Update the volume display."""
        self.volume = volume
        self.query_one("#volume-bar", ProgressBar).update(progress=volume)
        self.query_one("#volume-value", Static).update(f"{volume}%")


class FooterBar(Static):
    """Footer showing keyboard shortcuts."""

    def __init__(self, hints: list[tuple[str, str]] = None, **kwargs):
        super().__init__(**kwargs)
        self.hints = hints or [
            ("/", "Search"),
            ("Space", "Play/Pause"),
            ("+/-", "Volume"),
            ("n/p", "Next/Prev"),
            ("q", "Queue"),
            ("h", "History"),
            ("Esc", "Back"),
            ("Ctrl+C", "Quit"),
        ]

    def compose(self) -> ComposeResult:
        with Horizontal(id="footer"):
            for key, action in self.hints:
                yield Static(f"[{key}] {action}", classes="key-hint")


class LoadingIndicator(Static):
    """Loading indicator."""

    def compose(self) -> ComposeResult:
        yield Static("Loading...", classes="loading")


class EmptyState(Static):
    """Empty state message."""

    def __init__(self, message: str = "No data", **kwargs):
        super().__init__(**kwargs)
        self.message = message

    def compose(self) -> ComposeResult:
        yield Static(self.message, classes="empty-state")
