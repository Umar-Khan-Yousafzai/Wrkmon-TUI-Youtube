"""Data models for wrkmon."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Track:
    """Represents a track/video."""

    video_id: str
    title: str
    channel: str
    duration: int  # seconds
    thumbnail_url: Optional[str] = None
    id: Optional[int] = None

    @property
    def url(self) -> str:
        """Get YouTube URL."""
        return f"https://www.youtube.com/watch?v={self.video_id}"

    @property
    def duration_str(self) -> str:
        """Get formatted duration."""
        mins, secs = divmod(self.duration, 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            return f"{hours}:{mins:02d}:{secs:02d}"
        return f"{mins}:{secs:02d}"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "video_id": self.video_id,
            "title": self.title,
            "channel": self.channel,
            "duration": self.duration,
            "thumbnail_url": self.thumbnail_url,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Track":
        """Create from dictionary."""
        return cls(
            id=data.get("id"),
            video_id=data["video_id"],
            title=data["title"],
            channel=data["channel"],
            duration=data["duration"],
            thumbnail_url=data.get("thumbnail_url"),
        )


@dataclass
class Playlist:
    """Represents a playlist."""

    name: str
    description: str = ""
    tracks: list[Track] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    id: Optional[int] = None

    @property
    def track_count(self) -> int:
        """Get number of tracks."""
        return len(self.tracks)

    @property
    def total_duration(self) -> int:
        """Get total duration in seconds."""
        return sum(t.duration for t in self.tracks)

    @property
    def total_duration_str(self) -> str:
        """Get formatted total duration."""
        total = self.total_duration
        hours, remainder = divmod(total, 3600)
        mins, secs = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins}m {secs}s"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tracks": [t.to_dict() for t in self.tracks],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Playlist":
        """Create from dictionary."""
        return cls(
            id=data.get("id"),
            name=data["name"],
            description=data.get("description", ""),
            tracks=[Track.from_dict(t) for t in data.get("tracks", [])],
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )


@dataclass
class HistoryEntry:
    """Represents a play history entry."""

    track: Track
    played_at: datetime
    play_count: int = 1
    last_position: int = 0  # seconds, for resume
    completed: bool = False
    id: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "track": self.track.to_dict(),
            "played_at": self.played_at.isoformat(),
            "play_count": self.play_count,
            "last_position": self.last_position,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        """Create from dictionary."""
        return cls(
            id=data.get("id"),
            track=Track.from_dict(data["track"]),
            played_at=datetime.fromisoformat(data["played_at"]),
            play_count=data.get("play_count", 1),
            last_position=data.get("last_position", 0),
            completed=data.get("completed", False),
        )
