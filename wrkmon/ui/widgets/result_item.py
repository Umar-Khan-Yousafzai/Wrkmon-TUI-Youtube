"""Result item widget for displaying search results, queue items, etc."""

from textual.app import ComposeResult
from textual.widgets import ListItem, Label

from wrkmon.core.youtube import SearchResult
from wrkmon.utils.stealth import get_stealth


class ResultItem(ListItem):
    """A list item representing a search result or track."""

    def __init__(
        self,
        result: SearchResult,
        index: int,
        status: str = "READY",
        show_duration: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.result = result
        self.index = index
        self.status = status
        self.show_duration = show_duration
        self._stealth = get_stealth()

    def compose(self) -> ComposeResult:
        process_name = self._stealth.get_fake_process_name(self.result.title)
        pid = self._stealth.get_fake_pid()

        if self.show_duration:
            duration = self._stealth.format_duration(self.result.duration)
            text = f"{self.index:>2}  {process_name:<38}  {pid:>5}  {duration:>7}  {self.status}"
        else:
            text = f"{self.index:>2}  {process_name:<42}  {pid:>5}  {self.status}"

        yield Label(text, classes="result-text")


class QueueItem(ListItem):
    """A list item representing a queue entry."""

    def __init__(
        self,
        title: str,
        duration: int,
        index: int,
        is_current: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.title = title
        self.duration = duration
        self.index = index
        self.is_current = is_current
        self._stealth = get_stealth()

    def compose(self) -> ComposeResult:
        process_name = self._stealth.get_fake_process_name(self.title)
        duration = self._stealth.format_duration(self.duration)
        status = "RUNNING" if self.is_current else "QUEUED"
        marker = "▶" if self.is_current else " "

        text = f"{marker} {self.index:>2}  {process_name:<40}  {duration:>7}  {status}"
        yield Label(text, classes="queue-text")


class HistoryItem(ListItem):
    """A list item representing a history entry."""

    def __init__(
        self,
        title: str,
        duration: int,
        play_count: int,
        last_played: str,
        index: int,
        video_id: str,
        channel: str,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.title = title
        self.duration = duration
        self.play_count = play_count
        self.last_played = last_played
        self.index = index
        self.video_id = video_id
        self.channel = channel
        self._stealth = get_stealth()

    def compose(self) -> ComposeResult:
        process_name = self._stealth.get_fake_process_name(self.title)[:32]
        duration = self._stealth.format_duration(self.duration)

        text = f"{self.index:>2}  {process_name:<34}  {duration:>7}  {self.play_count:>3}x  {self.last_played}"
        yield Label(text, classes="history-text")
