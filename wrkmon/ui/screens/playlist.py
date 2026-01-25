"""Playlist screen for wrkmon."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical
from textual.widgets import Static, ListView, ListItem, Label, Input
from textual.binding import Binding
from textual import on

from wrkmon.data.models import Playlist, Track


class PlaylistListItem(ListItem):
    """A playlist list item."""

    def __init__(self, playlist: Playlist, index: int, **kwargs):
        super().__init__(**kwargs)
        self.playlist = playlist
        self.index = index

    def compose(self) -> ComposeResult:
        track_count = self.playlist.track_count
        duration = self.playlist.total_duration_str
        text = f"{self.index:2}  {self.playlist.name:<40} {track_count:>4} tracks  {duration:>10}"
        yield Label(text)


class TrackListItem(ListItem):
    """A track list item within a playlist."""

    def __init__(self, track: Track, index: int, **kwargs):
        super().__init__(**kwargs)
        self.track = track
        self.index = index

    def compose(self) -> ComposeResult:
        from wrkmon.utils.stealth import get_stealth
        stealth = get_stealth()

        process_name = stealth.get_fake_process_name(self.track.title)[:40]
        duration = self.track.duration_str
        text = f"  {self.index:2}  {process_name:<40} {duration:>8}"
        yield Label(text)


class PlaylistScreen(Screen):
    """Playlist management screen."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=False),
        Binding("enter", "select_item", "Select", show=False),
        Binding("n", "new_playlist", "New Playlist", show=False),
        Binding("d", "delete_item", "Delete", show=False),
        Binding("p", "play_all", "Play All", show=False),
        Binding("a", "add_to_queue", "Add to Queue", show=False),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.playlists: list[Playlist] = []
        self.current_playlist: Playlist | None = None
        self.viewing_tracks = False

    def compose(self) -> ComposeResult:
        with Vertical(id="playlist-screen"):
            yield Static("PLAYLISTS", id="playlist-header")
            yield Static(
                " #   Name                                         Tracks     Duration",
                id="playlist-list-header",
            )
            yield ListView(id="playlist-list")
            yield Input(
                placeholder="Enter playlist name...",
                id="playlist-name-input",
            )
            yield Static("", id="playlist-status")

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.query_one("#playlist-name-input", Input).display = False
        self.load_playlists()

    def load_playlists(self) -> None:
        """Load all playlists."""
        db = self.app.database
        self.playlists = db.get_all_playlists()
        self.display_playlists()

    def display_playlists(self) -> None:
        """Display playlist list."""
        self.viewing_tracks = False
        self.current_playlist = None

        header = self.query_one("#playlist-header", Static)
        header.update("PLAYLISTS")

        list_header = self.query_one("#playlist-list-header", Static)
        list_header.update(
            " #   Name                                         Tracks     Duration"
        )

        list_view = self.query_one("#playlist-list", ListView)
        list_view.clear()

        if not self.playlists:
            self.update_status("No playlists. Press 'n' to create one.")
            return

        for i, playlist in enumerate(self.playlists, 1):
            list_view.append(PlaylistListItem(playlist, i))

        self.update_status(f"{len(self.playlists)} playlists")

    def display_tracks(self, playlist: Playlist) -> None:
        """Display tracks in a playlist."""
        self.viewing_tracks = True
        self.current_playlist = playlist

        # Load full playlist with tracks
        full_playlist = self.app.database.get_playlist(playlist.id)
        if full_playlist:
            self.current_playlist = full_playlist

        header = self.query_one("#playlist-header", Static)
        header.update(f"PLAYLIST: {playlist.name}")

        list_header = self.query_one("#playlist-list-header", Static)
        list_header.update(
            " #   Process Name                                  Duration"
        )

        list_view = self.query_one("#playlist-list", ListView)
        list_view.clear()

        if not self.current_playlist.tracks:
            self.update_status("Playlist empty")
            return

        for i, track in enumerate(self.current_playlist.tracks, 1):
            list_view.append(TrackListItem(track, i))

        self.update_status(
            f"{len(self.current_playlist.tracks)} tracks - "
            f"{self.current_playlist.total_duration_str}"
        )

    def update_status(self, message: str) -> None:
        """Update status message."""
        self.query_one("#playlist-status", Static).update(message)

    def action_go_back(self) -> None:
        """Go back."""
        if self.viewing_tracks:
            self.display_playlists()
        else:
            self.app.pop_screen()

    def action_select_item(self) -> None:
        """Select the current item."""
        list_view = self.query_one("#playlist-list", ListView)
        if list_view.highlighted_child is None:
            return

        item = list_view.highlighted_child

        if isinstance(item, PlaylistListItem):
            self.display_tracks(item.playlist)
        elif isinstance(item, TrackListItem):
            # Play the track
            from wrkmon.core.youtube import SearchResult
            result = SearchResult(
                video_id=item.track.video_id,
                title=item.track.title,
                channel=item.track.channel,
                duration=item.track.duration,
                view_count=0,
            )
            self.app.call_later(self.app.play_track, result)

    def action_new_playlist(self) -> None:
        """Create a new playlist."""
        if self.viewing_tracks:
            return

        name_input = self.query_one("#playlist-name-input", Input)
        name_input.display = True
        name_input.focus()

    @on(Input.Submitted, "#playlist-name-input")
    def handle_playlist_name(self, event: Input.Submitted) -> None:
        """Handle playlist name submission."""
        name = event.value.strip()
        name_input = self.query_one("#playlist-name-input", Input)
        name_input.display = False
        name_input.value = ""

        if not name:
            return

        # Create playlist
        db = self.app.database
        try:
            playlist = db.create_playlist(name)
            self.playlists.append(playlist)
            self.display_playlists()
            self.update_status(f"Created playlist: {name}")
        except Exception as e:
            self.update_status(f"Error: {e}")

    def action_delete_item(self) -> None:
        """Delete the selected item."""
        list_view = self.query_one("#playlist-list", ListView)
        if list_view.highlighted_child is None:
            return

        item = list_view.highlighted_child
        db = self.app.database

        if isinstance(item, PlaylistListItem):
            # Delete playlist
            if db.delete_playlist(item.playlist.id):
                self.load_playlists()
                self.update_status(f"Deleted playlist: {item.playlist.name}")
        elif isinstance(item, TrackListItem) and self.current_playlist:
            # Remove track from playlist
            if db.remove_track_from_playlist(self.current_playlist.id, item.track.id):
                self.display_tracks(self.current_playlist)
                self.update_status(f"Removed track")

    async def action_play_all(self) -> None:
        """Play all tracks in current playlist."""
        if not self.current_playlist or not self.current_playlist.tracks:
            return

        # Add all to queue and play
        for track in self.current_playlist.tracks:
            from wrkmon.core.youtube import SearchResult
            result = SearchResult(
                video_id=track.video_id,
                title=track.title,
                channel=track.channel,
                duration=track.duration,
                view_count=0,
            )
            self.app.add_to_queue(result)

        # Play first
        first = self.current_playlist.tracks[0]
        from wrkmon.core.youtube import SearchResult
        result = SearchResult(
            video_id=first.video_id,
            title=first.title,
            channel=first.channel,
            duration=first.duration,
            view_count=0,
        )
        await self.app.play_track(result)
        self.update_status("Playing playlist")

    def action_add_to_queue(self) -> None:
        """Add selected track to queue."""
        list_view = self.query_one("#playlist-list", ListView)
        if list_view.highlighted_child is None:
            return

        item = list_view.highlighted_child

        if isinstance(item, TrackListItem):
            from wrkmon.core.youtube import SearchResult
            result = SearchResult(
                video_id=item.track.video_id,
                title=item.track.title,
                channel=item.track.channel,
                duration=item.track.duration,
                view_count=0,
            )
            self.app.add_to_queue(result)
            self.update_status(f"Added to queue: {item.track.title[:30]}...")
