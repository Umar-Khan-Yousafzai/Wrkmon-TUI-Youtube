"""Header bar widget for wrkmon."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Static

from wrkmon.utils.stealth import get_stealth


class HeaderBar(Static):
    """Application header with title and fake system stats."""

    cpu = reactive(23)
    mem = reactive(45)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._stealth = get_stealth()

    def compose(self) -> ComposeResult:
        with Horizontal(id="header-inner"):
            yield Static("WRKMON", id="app-title")
            yield Static("", id="current-view")
            yield Static(self._format_stats(), id="sys-stats")

    def _format_stats(self) -> str:
        return f"CPU:{self.cpu:>3}%  MEM:{self.mem:>3}%"

    def on_mount(self) -> None:
        """Start periodic stats updates."""
        self.set_interval(3.0, self._update_stats)

    def _update_stats(self) -> None:
        """Update fake system stats."""
        self.cpu = self._stealth.get_fake_cpu()
        self.mem = self._stealth.get_fake_memory()

    def watch_cpu(self) -> None:
        """React to CPU changes."""
        self._refresh_stats()

    def watch_mem(self) -> None:
        """React to memory changes."""
        self._refresh_stats()

    def _refresh_stats(self) -> None:
        """Update the stats display."""
        try:
            self.query_one("#sys-stats", Static).update(self._format_stats())
        except Exception:
            pass

    def set_view_name(self, name: str) -> None:
        """Update the current view indicator."""
        try:
            self.query_one("#current-view", Static).update(f"/{name.upper()}")
        except Exception:
            pass
