"""Custom Textual messages for wrkmon component communication."""

from textual.message import Message

from wrkmon.core.youtube import SearchResult


class TrackSelected(Message):
    """Emitted when a track is selected for playback."""

    def __init__(self, result: SearchResult) -> None:
        self.result = result
        super().__init__()


class TrackQueued(Message):
    """Emitted when a track is added to queue."""

    def __init__(self, result: SearchResult) -> None:
        self.result = result
        super().__init__()


class PlaybackStateChanged(Message):
    """Emitted when playback state changes."""

    def __init__(
        self,
        is_playing: bool,
        position: float = 0.0,
        duration: float = 0.0,
        title: str = "",
    ) -> None:
        self.is_playing = is_playing
        self.position = position
        self.duration = duration
        self.title = title
        super().__init__()


class VolumeChanged(Message):
    """Emitted when volume changes."""

    def __init__(self, volume: int) -> None:
        self.volume = volume
        super().__init__()


class ViewChanged(Message):
    """Emitted when the active view should change."""

    def __init__(self, view_name: str) -> None:
        self.view_name = view_name
        super().__init__()


class SearchStarted(Message):
    """Emitted when a search begins."""

    def __init__(self, query: str) -> None:
        self.query = query
        super().__init__()


class SearchCompleted(Message):
    """Emitted when search results are ready."""

    def __init__(self, results: list[SearchResult], query: str) -> None:
        self.results = results
        self.query = query
        super().__init__()


class QueueUpdated(Message):
    """Emitted when the queue changes."""

    def __init__(self, queue_length: int, current_index: int) -> None:
        self.queue_length = queue_length
        self.current_index = current_index
        super().__init__()


class StatusMessage(Message):
    """Emitted to show a status message to the user."""

    def __init__(self, message: str, level: str = "info") -> None:
        self.message = message
        self.level = level  # "info", "success", "warning", "error"
        super().__init__()


class SpeedChanged(Message):
    """Emitted when playback speed changes."""

    def __init__(self, speed: float) -> None:
        self.speed = speed
        super().__init__()


class EqualizerChanged(Message):
    """Emitted when equalizer preset changes."""

    def __init__(self, preset: str) -> None:
        self.preset = preset
        super().__init__()


class SleepTimerSet(Message):
    """Emitted when sleep timer is set or cancelled."""

    def __init__(self, minutes: int, active: bool) -> None:
        self.minutes = minutes
        self.active = active
        super().__init__()


class AutoplayToggled(Message):
    """Emitted when autoplay/radio mode is toggled."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled
        super().__init__()


class AddToPlaylist(Message):
    """Emitted to add a track to a playlist."""

    def __init__(self, result: SearchResult, playlist_id: int) -> None:
        self.result = result
        self.playlist_id = playlist_id
        super().__init__()
