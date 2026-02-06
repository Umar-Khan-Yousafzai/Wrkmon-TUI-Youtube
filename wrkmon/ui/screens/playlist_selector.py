"""Playlist selection modal for wrkmon."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Static, ListView, ListItem, Label, Input
from textual.binding import Binding
from textual import on

from wrkmon.data.models import Playlist


class PlaylistOptionItem(ListItem):
    """A selectable playlist item in the selector modal."""

    def __init__(self, playlist: Playlist, index: int, **kwargs):
        super().__init__(**kwargs)
        self.playlist = playlist
        self.index = index

    def compose(self) -> ComposeResult:
        track_count = self.playlist.track_count
        text = f"  {self.index:2}  {self.playlist.name:<40} {track_count:>4} tracks"
        yield Label(text)


class PlaylistSelectorScreen(ModalScreen):
    """Modal screen for selecting a playlist to add a track to."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    DEFAULT_CSS = """
    PlaylistSelectorScreen {
        align: center middle;
    }

    #playlist-selector-container {
        width: 60;
        height: auto;
        max-height: 80%;
        background: #161b22;
        border: thick #30363d;
        padding: 1 2;
    }

    #selector-title {
        text-align: center;
        color: #58a6ff;
        text-style: bold;
        padding-bottom: 1;
    }

    #selector-track-label {
        color: #8b949e;
        padding-bottom: 1;
    }

    #selector-playlist-list {
        height: auto;
        max-height: 15;
        background: #0d1117;
        scrollbar-background: #161b22;
        scrollbar-color: #30363d;
    }

    #selector-empty-label {
        color: #6e7681;
        padding: 1 2;
    }

    #selector-new-label {
        color: #a371f7;
        text-style: bold;
        padding: 1 0 0 0;
    }

    #selector-new-input {
        width: 100%;
        background: #0d1117;
        border: tall #30363d;
        color: #f0f6fc;
    }

    #selector-new-input:focus {
        border: tall #58a6ff;
    }

    #selector-hint {
        color: #6e7681;
        padding-top: 1;
    }
    """

    def __init__(self, track_title: str, **kwargs):
        super().__init__(**kwargs)
        self.track_title = track_title
        self.playlists: list[Playlist] = []

    def compose(self) -> ComposeResult:
        with Container(id="playlist-selector-container"):
            yield Static("Add to Playlist", id="selector-title")
            yield Static(
                f"Track: {self.track_title[:50]}{'...' if len(self.track_title) > 50 else ''}",
                id="selector-track-label",
            )
            yield ListView(id="selector-playlist-list")
            yield Static("", id="selector-empty-label")
            yield Static("New playlist:", id="selector-new-label")
            yield Input(
                placeholder="Enter playlist name...",
                id="selector-new-input",
            )
            yield Static(
                "[dim]Enter[/] select | [dim]Escape[/] cancel",
                id="selector-hint",
                markup=True,
            )

    def on_mount(self) -> None:
        self.playlists = self.app.database.get_all_playlists()
        self._populate_list()

    def _populate_list(self) -> None:
        list_view = self.query_one("#selector-playlist-list", ListView)
        empty_label = self.query_one("#selector-empty-label", Static)
        list_view.clear()
        if not self.playlists:
            empty_label.update("No existing playlists")
            list_view.display = False
        else:
            empty_label.update("")
            list_view.display = True
            for i, playlist in enumerate(self.playlists, 1):
                list_view.append(PlaylistOptionItem(playlist, i))
            list_view.focus()

    @on(ListView.Selected, "#selector-playlist-list")
    def handle_playlist_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, PlaylistOptionItem):
            self.dismiss(item.playlist.id)

    @on(Input.Submitted, "#selector-new-input")
    def handle_new_playlist(self, event: Input.Submitted) -> None:
        name = event.value.strip()
        if not name:
            return
        try:
            db = self.app.database
            new_playlist = db.create_playlist(name)
            self.dismiss(new_playlist.id)
        except Exception:
            event.input.value = ""

    def action_cancel(self) -> None:
        self.dismiss(None)
