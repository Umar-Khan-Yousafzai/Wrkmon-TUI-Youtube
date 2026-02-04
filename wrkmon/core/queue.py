"""Play queue management."""

import random
from dataclasses import dataclass, field
from typing import Optional

from wrkmon.core.youtube import SearchResult


@dataclass
class QueueItem:
    """An item in the play queue."""

    video_id: str
    title: str
    channel: str
    duration: int
    added_at: float = 0.0
    playback_position: int = 0  # Last played position in seconds

    @classmethod
    def from_search_result(cls, result: SearchResult) -> "QueueItem":
        """Create a queue item from a search result."""
        import time

        return cls(
            video_id=result.video_id,
            title=result.title,
            channel=result.channel,
            duration=result.duration,
            added_at=time.time(),
            playback_position=0,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "QueueItem":
        """Create a queue item from a dictionary."""
        import time

        return cls(
            video_id=data["video_id"],
            title=data["title"],
            channel=data["channel"],
            duration=data["duration"],
            added_at=data.get("added_at", time.time()),
            playback_position=data.get("playback_position", 0),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "video_id": self.video_id,
            "title": self.title,
            "channel": self.channel,
            "duration": self.duration,
            "added_at": self.added_at,
            "playback_position": self.playback_position,
        }

    @property
    def url(self) -> str:
        """Get the YouTube URL."""
        return f"https://www.youtube.com/watch?v={self.video_id}"


@dataclass
class PlayQueue:
    """Manages the play queue."""

    items: list[QueueItem] = field(default_factory=list)
    current_index: int = -1
    shuffle_mode: bool = False
    repeat_mode: str = "none"  # none, one, all
    _shuffle_order: list[int] = field(default_factory=list)

    @property
    def current(self) -> Optional[QueueItem]:
        """Get the current item."""
        if 0 <= self.current_index < len(self.items):
            if self.shuffle_mode and self._shuffle_order:
                actual_index = self._shuffle_order[self.current_index]
                return self.items[actual_index]
            return self.items[self.current_index]
        return None

    @property
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self.items) == 0

    @property
    def length(self) -> int:
        """Get queue length."""
        return len(self.items)

    @property
    def has_next(self) -> bool:
        """Check if there's a next item."""
        if self.repeat_mode == "all":
            return len(self.items) > 0
        if self.repeat_mode == "one":
            return self.current is not None
        return self.current_index < len(self.items) - 1

    @property
    def has_previous(self) -> bool:
        """Check if there's a previous item."""
        if self.repeat_mode in ("all", "one"):
            return len(self.items) > 0
        return self.current_index > 0

    def add(self, item: QueueItem) -> int:
        """Add an item to the queue. Returns position."""
        self.items.append(item)
        if self.shuffle_mode:
            self._shuffle_order.append(len(self.items) - 1)
        return len(self.items) - 1

    def add_search_result(self, result: SearchResult) -> int:
        """Add a search result to the queue."""
        return self.add(QueueItem.from_search_result(result))

    def add_multiple(self, items: list[QueueItem]) -> None:
        """Add multiple items to the queue."""
        for item in items:
            self.add(item)

    def remove(self, index: int) -> Optional[QueueItem]:
        """Remove an item by index."""
        if 0 <= index < len(self.items):
            item = self.items.pop(index)

            # Update shuffle order
            if self.shuffle_mode:
                self._shuffle_order = [i for i in self._shuffle_order if i != index]
                self._shuffle_order = [i - 1 if i > index else i for i in self._shuffle_order]

            # Update current index
            if index < self.current_index:
                self.current_index -= 1
            elif index == self.current_index:
                # Current item was removed
                if self.current_index >= len(self.items):
                    self.current_index = len(self.items) - 1

            return item
        return None

    def clear(self) -> None:
        """Clear the queue."""
        self.items.clear()
        self._shuffle_order.clear()
        self.current_index = -1

    def next(self) -> Optional[QueueItem]:
        """Move to and return the next item."""
        if not self.items:
            return None

        if self.repeat_mode == "one":
            return self.current

        if self.shuffle_mode:
            if self.current_index < len(self._shuffle_order) - 1:
                self.current_index += 1
            elif self.repeat_mode == "all":
                self.current_index = 0
            else:
                return None
        else:
            if self.current_index < len(self.items) - 1:
                self.current_index += 1
            elif self.repeat_mode == "all":
                self.current_index = 0
            else:
                return None

        return self.current

    def previous(self) -> Optional[QueueItem]:
        """Move to and return the previous item."""
        if not self.items:
            return None

        if self.repeat_mode == "one":
            return self.current

        if self.current_index > 0:
            self.current_index -= 1
        elif self.repeat_mode == "all":
            self.current_index = len(self.items) - 1
        else:
            return None

        return self.current

    def jump_to(self, index: int) -> Optional[QueueItem]:
        """Jump to a specific index."""
        if 0 <= index < len(self.items):
            self.current_index = index
            return self.current
        return None

    def shuffle(self) -> None:
        """Enable shuffle mode and create shuffle order."""
        self.shuffle_mode = True
        self._create_shuffle_order()

    def unshuffle(self) -> None:
        """Disable shuffle mode."""
        self.shuffle_mode = False
        # Update current index to actual position
        if self._shuffle_order and 0 <= self.current_index < len(self._shuffle_order):
            self.current_index = self._shuffle_order[self.current_index]
        self._shuffle_order.clear()

    def toggle_shuffle(self) -> bool:
        """Toggle shuffle mode. Returns new state."""
        if self.shuffle_mode:
            self.unshuffle()
        else:
            self.shuffle()
        return self.shuffle_mode

    def _create_shuffle_order(self) -> None:
        """Create a new shuffle order."""
        self._shuffle_order = list(range(len(self.items)))
        random.shuffle(self._shuffle_order)

        # Move current item to front if playing
        if self.current_index >= 0:
            current_actual = self.current_index
            if current_actual in self._shuffle_order:
                self._shuffle_order.remove(current_actual)
                self._shuffle_order.insert(0, current_actual)
                self.current_index = 0

    def set_repeat(self, mode: str) -> None:
        """Set repeat mode: none, one, all."""
        if mode in ("none", "one", "all"):
            self.repeat_mode = mode

    def cycle_repeat(self) -> str:
        """Cycle through repeat modes. Returns new mode."""
        modes = ["none", "one", "all"]
        current_idx = modes.index(self.repeat_mode)
        self.repeat_mode = modes[(current_idx + 1) % len(modes)]
        return self.repeat_mode

    def move(self, from_index: int, to_index: int) -> bool:
        """Move an item from one position to another."""
        if not (0 <= from_index < len(self.items) and 0 <= to_index < len(self.items)):
            return False

        item = self.items.pop(from_index)
        self.items.insert(to_index, item)

        # Update current index
        if self.current_index == from_index:
            self.current_index = to_index
        elif from_index < self.current_index <= to_index:
            self.current_index -= 1
        elif to_index <= self.current_index < from_index:
            self.current_index += 1

        # Recreate shuffle order if needed
        if self.shuffle_mode:
            self._create_shuffle_order()

        return True

    def get_upcoming(self, count: int = 5) -> list[QueueItem]:
        """Get upcoming items in queue."""
        result = []
        start = self.current_index + 1

        if self.shuffle_mode and self._shuffle_order:
            for i in range(start, min(start + count, len(self._shuffle_order))):
                actual_idx = self._shuffle_order[i]
                result.append(self.items[actual_idx])
        else:
            for i in range(start, min(start + count, len(self.items))):
                result.append(self.items[i])

        return result

    def to_list(self) -> list[QueueItem]:
        """Get all items in current play order."""
        if self.shuffle_mode and self._shuffle_order:
            return [self.items[i] for i in self._shuffle_order]
        return list(self.items)

    def update_playback_position(self, video_id: str, position: int) -> None:
        """Update the playback position for a queue item."""
        for item in self.items:
            if item.video_id == video_id:
                item.playback_position = position
                break

    def get_playback_position(self, video_id: str) -> int:
        """Get the saved playback position for a queue item."""
        for item in self.items:
            if item.video_id == video_id:
                return item.playback_position
        return 0

    def to_dict_list(self) -> list[dict]:
        """Convert all items to list of dicts for serialization."""
        return [item.to_dict() for item in self.items]

    def load_from_dicts(self, items: list[dict], current_index: int = -1) -> None:
        """Load queue from list of dicts."""
        self.clear()
        for data in items:
            item = QueueItem.from_dict(data)
            self.items.append(item)
        self.current_index = current_index if -1 <= current_index < len(self.items) else -1
        if self.shuffle_mode:
            self._create_shuffle_order()
