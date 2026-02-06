"""Help overlay screen for wrkmon."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static
from textual.binding import Binding


HELP_TEXT = """
[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]
[bold cyan]                    WRKMON KEYBOARD SHORTCUTS[/]
[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]

[bold orange1]NAVIGATION[/]
  [bold purple]F1[/]          Switch to Search view
  [bold purple]F2[/]          Switch to Queue view
  [bold purple]F3[/]          Switch to History view
  [bold purple]F4[/]          Switch to Playlists view
  [bold purple]j / ↓[/]       Move down in list
  [bold purple]k / ↑[/]       Move up in list
  [bold purple]g / Home[/]    Jump to top of list
  [bold purple]G / End[/]     Jump to bottom of list
  [bold purple]Tab[/]         Next focusable element
  [bold purple]Shift+Tab[/]   Previous focusable element

[bold orange1]PLAYBACK[/]
  [bold purple]F5 / Space[/]  Play / Pause
  [bold purple]F6 / -[/]      Volume down
  [bold purple]F7 / + =[/]    Volume up
  [bold purple]F8 / n[/]      Next track
  [bold purple]p[/]           Previous track
  [bold purple]F9 / s[/]      Stop playback
  [bold purple]r[/]           Cycle repeat mode (Off → One → All)
  [bold purple]m[/]           Mute / Unmute
  [bold purple]] [/]          Speed up (0.1x)
  [bold purple][ [/]          Speed down (0.1x)

[bold orange1]FEATURES[/]
  [bold purple]l[/]           Show lyrics for current track
  [bold purple]b[/]           Focus mode (clean screen)
  [bold purple]d[/]           Download current track
  [bold purple]a[/]           Toggle autoplay / radio mode
  [bold purple]t[/]           Theme picker

[bold orange1]SEARCH & QUEUE[/]
  [bold purple]/[/]           Focus search input
  [bold purple]Enter[/]       Play selected track
  [bold purple]F10[/]         Add highlighted to queue
  [bold purple]d / Del[/]     Remove from queue
  [bold purple]c[/]           Clear queue

[bold orange1]APPLICATION[/]
  [bold purple]?[/]           Show this help
  [bold purple]Escape[/]      Close overlay / Go back
  [bold purple]Ctrl+Q[/]      Quit application
  [bold purple]Ctrl+C[/]      Quit application

[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]
[dim]Press [bold]Escape[/bold] or [bold]?[/bold] to close this help[/]
"""


class HelpScreen(ModalScreen):
    """Modal help screen showing keyboard shortcuts."""

    BINDINGS = [
        Binding("escape", "close", "Close", show=False),
        Binding("?", "close", "Close", show=False),
        Binding("q", "close", "Close", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="help-container"):
            yield Static("[bold cyan]⌨  KEYBOARD SHORTCUTS[/]", id="help-title")
            with VerticalScroll(id="help-scroll"):
                yield Static(HELP_TEXT, id="help-content", markup=True)

    def action_close(self) -> None:
        """Close the help screen."""
        self.dismiss()

    def on_click(self) -> None:
        """Close on click outside."""
        self.dismiss()
