"""Playlists view container for wrkmon."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, ListView, ListItem, Label, Input
from textual.binding import Binding
from textual import on

from wrkmon.core.youtube import SearchResult
from wrkmon.data.models import Playlist, Track
from wrkmon.ui.messages import TrackSelected, TrackQueued, StatusMessage
from wrkmon.utils.stealth import get_stealth


class PlaylistItem(ListItem):
    """List item for a playlist."""

    def __init__(self, playlist: Playlist, index: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self.playlist = playlist
        self.index = index

    def compose(self) -> ComposeResult:
        count = self.playlist.track_count
        duration = self.playlist.total_duration_str
        text = f"{self.index:>2}  {self.playlist.name:<42}  {count:>4} tracks  {duration:>8}"
        yield Label(text)


class TrackItem(ListItem):
    """List item for a track in a playlist."""

    def __init__(self, track: Track, index: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self.track = track
        self.index = index
        self._stealth = get_stealth()

    def compose(self) -> ComposeResult:
        process_name = self._stealth.get_fake_process_name(self.track.title)[:40]
        duration = self.track.duration_str
        text = f"  {self.index:>2}  {process_name:<40}  {duration:>8}"
        yield Label(text)


class PlaylistsView(Vertical):
    """Playlists view - manage playlists and their tracks."""

    BINDINGS = [
        Binding("a", "queue_selected", "Add to Queue", show=True),
        Binding("n", "new_playlist", "New Playlist", show=True),
        Binding("d", "delete_item", "Delete", show=True),
        Binding("p", "play_all", "Play All", show=True),
        Binding("escape", "go_back", "Back", show=True),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.playlists: list[Playlist] = []
        self.current_playlist: Playlist | None = None
        self.viewing_tracks = False

    def compose(self) -> ComposeResult:
        yield Static("PLAYLISTS", id="view-title")

        yield Static(
            " #   Name                                          Tracks    Duration",
            id="list-header",
        )

        yield ListView(id="playlist-list")

        yield Input(
            placeholder="Enter playlist name...",
            id="new-playlist-input",
        )

        yield Static("Loading playlists...", id="status-bar")

    def on_mount(self) -> None:
        """Load playlists on mount."""
        self.query_one("#new-playlist-input", Input).display = False
        self.load_playlists()

    def load_playlists(self) -> None:
        """Load all playlists."""
        try:
            db = self.app.database
            self.playlists = db.get_all_playlists()
            self._display_playlists()
        except Exception as e:
            self._update_status(f"Failed to load: {e}")

    def _display_playlists(self) -> None:
        """Display playlist list."""
        self.viewing_tracks = False
        self.current_playlist = None

        self.query_one("#view-title", Static).update("PLAYLISTS")
        self.query_one("#list-header", Static).update(
            " #   Name                                          Tracks    Duration"
        )

        list_view = self.query_one("#playlist-list", ListView)
        list_view.clear()

        if not self.playlists:
            self._update_status("No playlists. Press 'n' to create one.")
            return

        for i, playlist in enumerate(self.playlists, 1):
            list_view.append(PlaylistItem(playlist, i))

        self._update_status(f"{len(self.playlists)} playlists")

    def _display_tracks(self, playlist: Playlist) -> None:
        """Display tracks in a playlist."""
        self.viewing_tracks = True
        self.current_playlist = playlist

        # Load full playlist with tracks
        try:
            full_playlist = self.app.database.get_playlist(playlist.id)
            if full_playlist:
                self.current_playlist = full_playlist
        except Exception:
            pass

        self.query_one("#view-title", Static).update(f"PLAYLIST: {playlist.name}")
        self.query_one("#list-header", Static).update(
            "   #   Process                                      Duration"
        )

        list_view = self.query_one("#playlist-list", ListView)
        list_view.clear()

        if not self.current_playlist.tracks:
            self._update_status("Playlist empty")
            return

        for i, track in enumerate(self.current_playlist.tracks, 1):
            list_view.append(TrackItem(track, i))

        self._update_status(
            f"{len(self.current_playlist.tracks)} tracks - "
            f"{self.current_playlist.total_duration_str}"
        )

    def _update_status(self, message: str) -> None:
        """Update status bar."""
        try:
            self.query_one("#status-bar", Static).update(message)
        except Exception:
            pass

    def _track_to_result(self, track: Track) -> SearchResult:
        """Convert a Track to SearchResult."""
        return SearchResult(
            video_id=track.video_id,
            title=track.title,
            channel=track.channel,
            duration=track.duration,
            view_count=0,
        )

    def action_go_back(self) -> None:
        """Go back to playlist list."""
        if self.viewing_tracks:
            self._display_playlists()

    @on(ListView.Selected, "#playlist-list")
    def handle_item_selected(self, event: ListView.Selected) -> None:
        """Handle Enter key - open playlist or play track."""
        item = event.item

        if isinstance(item, PlaylistItem):
            self._display_tracks(item.playlist)
        elif isinstance(item, TrackItem):
            result = self._track_to_result(item.track)
            self.post_message(TrackSelected(result))
            self._update_status(f"Playing: {item.track.title[:40]}...")

    def action_new_playlist(self) -> None:
        """Create a new playlist."""
        if self.viewing_tracks:
            return

        input_widget = self.query_one("#new-playlist-input", Input)
        input_widget.display = True
        input_widget.focus()

    @on(Input.Submitted, "#new-playlist-input")
    def handle_new_playlist(self, event: Input.Submitted) -> None:
        """Handle new playlist name submission."""
        name = event.value.strip()
        input_widget = self.query_one("#new-playlist-input", Input)
        input_widget.display = False
        input_widget.value = ""

        if not name:
            return

        try:
            db = self.app.database
            playlist = db.create_playlist(name)
            self.playlists.append(playlist)
            self._display_playlists()
            self.post_message(StatusMessage(f"Created: {name}", "success"))
        except Exception as e:
            self.post_message(StatusMessage(f"Error: {e}", "error"))

    def action_delete_item(self) -> None:
        """Delete selected item."""
        list_view = self.query_one("#playlist-list", ListView)
        if list_view.highlighted_child is None:
            return

        item = list_view.highlighted_child
        db = self.app.database

        try:
            if isinstance(item, PlaylistItem):
                if db.delete_playlist(item.playlist.id):
                    self.load_playlists()
                    self.post_message(StatusMessage(f"Deleted: {item.playlist.name}", "info"))
            elif isinstance(item, TrackItem) and self.current_playlist:
                if db.remove_track_from_playlist(self.current_playlist.id, item.track.id):
                    self._display_tracks(self.current_playlist)
                    self.post_message(StatusMessage("Track removed", "info"))
        except Exception as e:
            self.post_message(StatusMessage(f"Error: {e}", "error"))

    async def action_play_all(self) -> None:
        """Play all tracks in current playlist."""
        if not self.current_playlist or not self.current_playlist.tracks:
            return

        # Add all to queue
        for track in self.current_playlist.tracks:
            result = self._track_to_result(track)
            self.app.add_to_queue(result)

        # Play first
        first = self.current_playlist.tracks[0]
        result = self._track_to_result(first)
        self.post_message(TrackSelected(result))
        self._update_status("Playing playlist")

    def action_queue_selected(self) -> None:
        """Add selected track to queue."""
        list_view = self.query_one("#playlist-list", ListView)
        if list_view.highlighted_child is None:
            return

        item = list_view.highlighted_child
        if isinstance(item, TrackItem):
            result = self._track_to_result(item.track)
            self.post_message(TrackQueued(result))
            self._update_status(f"Queued: {item.track.title[:40]}...")
