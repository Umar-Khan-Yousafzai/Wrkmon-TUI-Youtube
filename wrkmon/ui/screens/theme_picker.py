"""Theme picker overlay screen for wrkmon."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Static, ListView, ListItem
from textual.binding import Binding
from textual import on

from wrkmon.ui.theme import THEMES


THEME_DISPLAY = {
    "github_dark": ("GitHub Dark", "Classic dark theme inspired by GitHub"),
    "matrix": ("Matrix", "Green-on-black hacker aesthetic"),
    "dracula": ("Dracula", "Purple-tinted dark theme with vivid accents"),
    "nord": ("Nord", "Arctic, cool-toned color palette"),
}


def _build_theme_preview(theme_id: str) -> str:
    colors = THEMES[theme_id]
    name, description = THEME_DISPLAY.get(theme_id, (theme_id, ""))
    primary = colors["primary"]
    secondary = colors["secondary"]
    accent = colors["accent"]
    success = colors["success"]
    warning = colors["warning"]
    error = colors["error"]
    return (
        f"[bold {primary}]{name}[/]  "
        f"[{secondary}]{description}[/]  "
        f"[on {primary}]  [/] "
        f"[on {accent}]  [/] "
        f"[on {success}]  [/] "
        f"[on {warning}]  [/] "
        f"[on {error}]  [/]"
    )


class ThemePickerScreen(ModalScreen):
    """Modal screen for selecting an application theme."""

    DEFAULT_CSS = """
    ThemePickerScreen {
        align: center middle;
    }

    #theme-picker-container {
        width: 72;
        height: auto;
        max-height: 80%;
        background: #161b22;
        border: thick #30363d;
        padding: 1 2;
    }

    #theme-picker-title {
        text-align: center;
        color: #58a6ff;
        text-style: bold;
        padding-bottom: 1;
    }

    #theme-picker-hint {
        text-align: center;
        color: #6e7681;
        padding-top: 1;
    }

    #theme-list {
        height: auto;
        max-height: 20;
        background: #0d1117;
        scrollbar-background: #161b22;
        scrollbar-color: #30363d;
        scrollbar-color-hover: #484f58;
    }

    #theme-list > ListItem {
        height: 2;
        padding: 0 1;
        color: #c9d1d9;
    }

    #theme-list > ListItem:hover {
        background: #161b22;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="theme-picker-container"):
            yield Static(
                "[bold cyan]Select Theme[/]",
                id="theme-picker-title",
                markup=True,
            )
            with ListView(id="theme-list"):
                for theme_id in THEMES:
                    preview_markup = _build_theme_preview(theme_id)
                    yield ListItem(
                        Static(preview_markup, markup=True),
                        name=theme_id,
                    )
            yield Static(
                "[dim]Enter[/dim] select  [dim]Escape[/dim] cancel",
                id="theme-picker-hint",
                markup=True,
            )

    @on(ListView.Selected)
    def on_theme_selected(self, event: ListView.Selected) -> None:
        self.dismiss(event.item.name)

    def action_cancel(self) -> None:
        self.dismiss(None)
