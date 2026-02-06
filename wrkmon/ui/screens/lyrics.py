"""Lyrics overlay screen for wrkmon."""

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static
from textual.binding import Binding


class LyricsScreen(ModalScreen):
    """Modal screen displaying song lyrics."""

    DEFAULT_CSS = """
    LyricsScreen {
        align: center middle;
    }

    #lyrics-container {
        width: 80;
        height: 80%;
        max-height: 90%;
        background: #161b22;
        border: thick #30363d;
        padding: 1 2;
    }

    #lyrics-title {
        text-align: center;
        color: #58a6ff;
        text-style: bold;
        padding-bottom: 1;
        width: 100%;
    }

    #lyrics-separator {
        text-align: center;
        color: #30363d;
        width: 100%;
    }

    #lyrics-scroll {
        height: 1fr;
        background: #161b22;
        scrollbar-background: #161b22;
        scrollbar-color: #30363d;
        scrollbar-color-hover: #484f58;
        scrollbar-color-active: #6e7681;
    }

    #lyrics-text {
        color: #c9d1d9;
        width: 100%;
        padding: 1 2;
    }

    #lyrics-no-content {
        color: #8b949e;
        text-align: center;
        width: 100%;
        padding: 3 2;
        text-style: italic;
    }

    #lyrics-footer {
        text-align: center;
        color: #6e7681;
        width: 100%;
        padding-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Close", show=False),
        Binding("l", "close", "Close", show=False),
    ]

    def __init__(self, title: str, lyrics: str) -> None:
        super().__init__()
        self._title = title
        self._lyrics = lyrics

    def compose(self) -> ComposeResult:
        with Container(id="lyrics-container"):
            yield Static(
                f"[bold cyan]\u266b  {self._title}[/]",
                id="lyrics-title",
                markup=True,
            )
            yield Static(
                "[dim]" + "\u2500" * 60 + "[/]",
                id="lyrics-separator",
                markup=True,
            )
            with VerticalScroll(id="lyrics-scroll"):
                if self._lyrics:
                    yield Static(
                        self._lyrics,
                        id="lyrics-text",
                    )
                else:
                    yield Static(
                        "[italic #8b949e]No lyrics found for this track[/]",
                        id="lyrics-no-content",
                        markup=True,
                    )
            yield Static(
                "[dim]Press [bold]Escape[/bold] or [bold]l[/bold] to close[/]",
                id="lyrics-footer",
                markup=True,
            )

    def action_close(self) -> None:
        self.dismiss()
