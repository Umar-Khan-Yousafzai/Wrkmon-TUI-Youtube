"""Audio URL and metadata caching."""

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from wrkmon.utils.config import get_config


@dataclass
class CachedStream:
    """Cached stream information."""

    video_id: str
    title: str
    channel: str
    duration: int
    audio_url: str
    thumbnail_url: Optional[str]
    cached_at: float
    expires_at: float

    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() > self.expires_at


class Cache:
    """Manages caching of audio URLs and metadata."""

    def __init__(self, db_path: Optional[Path] = None):
        config = get_config()
        self._db_path = db_path or config.cache_path
        self._ttl_hours = config.url_ttl_hours
        self._max_entries = config.get("cache", "max_entries", 1000)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the cache database."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stream_cache (
                    video_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    duration INTEGER NOT NULL,
                    audio_url TEXT NOT NULL,
                    thumbnail_url TEXT,
                    cached_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at ON stream_cache(expires_at)
            """)
            conn.commit()

    def get(self, video_id: str) -> Optional[CachedStream]:
        """Get a cached stream by video ID."""
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM stream_cache
                WHERE video_id = ? AND expires_at > ?
                """,
                (video_id, time.time()),
            )
            row = cursor.fetchone()

            if row:
                return CachedStream(
                    video_id=row["video_id"],
                    title=row["title"],
                    channel=row["channel"],
                    duration=row["duration"],
                    audio_url=row["audio_url"],
                    thumbnail_url=row["thumbnail_url"],
                    cached_at=row["cached_at"],
                    expires_at=row["expires_at"],
                )

        return None

    def set(
        self,
        video_id: str,
        title: str,
        channel: str,
        duration: int,
        audio_url: str,
        thumbnail_url: Optional[str] = None,
    ) -> CachedStream:
        """Cache a stream URL."""
        now = time.time()
        expires_at = now + (self._ttl_hours * 3600)

        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO stream_cache
                (video_id, title, channel, duration, audio_url, thumbnail_url, cached_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (video_id, title, channel, duration, audio_url, thumbnail_url, now, expires_at),
            )
            conn.commit()

        # Cleanup old entries if we're over the limit
        self._cleanup()

        return CachedStream(
            video_id=video_id,
            title=title,
            channel=channel,
            duration=duration,
            audio_url=audio_url,
            thumbnail_url=thumbnail_url,
            cached_at=now,
            expires_at=expires_at,
        )

    def delete(self, video_id: str) -> bool:
        """Delete a cache entry."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM stream_cache WHERE video_id = ?",
                (video_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def clear(self) -> int:
        """Clear all cache entries. Returns count deleted."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute("DELETE FROM stream_cache")
            conn.commit()
            return cursor.rowcount

    def clear_expired(self) -> int:
        """Clear expired cache entries. Returns count deleted."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM stream_cache WHERE expires_at <= ?",
                (time.time(),),
            )
            conn.commit()
            return cursor.rowcount

    def _cleanup(self) -> None:
        """Cleanup old entries if over the limit."""
        with sqlite3.connect(self._db_path) as conn:
            # First clear expired
            conn.execute(
                "DELETE FROM stream_cache WHERE expires_at <= ?",
                (time.time(),),
            )

            # Then check count
            cursor = conn.execute("SELECT COUNT(*) FROM stream_cache")
            count = cursor.fetchone()[0]

            if count > self._max_entries:
                # Delete oldest entries
                excess = count - self._max_entries
                conn.execute(
                    """
                    DELETE FROM stream_cache
                    WHERE video_id IN (
                        SELECT video_id FROM stream_cache
                        ORDER BY cached_at ASC
                        LIMIT ?
                    )
                    """,
                    (excess,),
                )

            conn.commit()

    def get_stats(self) -> dict:
        """Get cache statistics."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM stream_cache")
            total = cursor.fetchone()[0]

            cursor = conn.execute(
                "SELECT COUNT(*) FROM stream_cache WHERE expires_at > ?",
                (time.time(),),
            )
            valid = cursor.fetchone()[0]

            cursor = conn.execute(
                "SELECT SUM(LENGTH(audio_url)) FROM stream_cache"
            )
            size = cursor.fetchone()[0] or 0

        return {
            "total_entries": total,
            "valid_entries": valid,
            "expired_entries": total - valid,
            "approximate_size_bytes": size,
        }
