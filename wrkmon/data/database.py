"""Database operations for wrkmon."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from wrkmon.data.models import Track, Playlist, HistoryEntry
from wrkmon.data.migrations import run_migrations
from wrkmon.utils.config import get_config


class Database:
    """Database access layer for wrkmon."""

    def __init__(self, db_path: Optional[Path] = None):
        config = get_config()
        self._db_path = db_path or config.database_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database connection and run migrations."""
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        run_migrations(self._conn)

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    # ==================== Track Operations ====================

    def get_or_create_track(
        self,
        video_id: str,
        title: str,
        channel: str,
        duration: int,
        thumbnail_url: Optional[str] = None,
    ) -> Track:
        """Get existing track or create new one."""
        # Try to get existing
        cursor = self._conn.execute(
            "SELECT * FROM tracks WHERE video_id = ?",
            (video_id,),
        )
        row = cursor.fetchone()

        if row:
            return Track(
                id=row["id"],
                video_id=row["video_id"],
                title=row["title"],
                channel=row["channel"],
                duration=row["duration"],
                thumbnail_url=row["thumbnail_url"],
            )

        # Create new
        cursor = self._conn.execute(
            """
            INSERT INTO tracks (video_id, title, channel, duration, thumbnail_url)
            VALUES (?, ?, ?, ?, ?)
            """,
            (video_id, title, channel, duration, thumbnail_url),
        )
        self._conn.commit()

        return Track(
            id=cursor.lastrowid,
            video_id=video_id,
            title=title,
            channel=channel,
            duration=duration,
            thumbnail_url=thumbnail_url,
        )

    def get_track_by_video_id(self, video_id: str) -> Optional[Track]:
        """Get a track by video ID."""
        cursor = self._conn.execute(
            "SELECT * FROM tracks WHERE video_id = ?",
            (video_id,),
        )
        row = cursor.fetchone()

        if row:
            return Track(
                id=row["id"],
                video_id=row["video_id"],
                title=row["title"],
                channel=row["channel"],
                duration=row["duration"],
                thumbnail_url=row["thumbnail_url"],
            )
        return None

    # ==================== Playlist Operations ====================

    def create_playlist(self, name: str, description: str = "") -> Playlist:
        """Create a new playlist."""
        now = datetime.now()
        cursor = self._conn.execute(
            """
            INSERT INTO playlists (name, description, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (name, description, now, now),
        )
        self._conn.commit()

        return Playlist(
            id=cursor.lastrowid,
            name=name,
            description=description,
            tracks=[],
            created_at=now,
            updated_at=now,
        )

    def get_playlist(self, playlist_id: int) -> Optional[Playlist]:
        """Get a playlist by ID with its tracks."""
        cursor = self._conn.execute(
            "SELECT * FROM playlists WHERE id = ?",
            (playlist_id,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        # Get tracks
        cursor = self._conn.execute(
            """
            SELECT t.* FROM tracks t
            JOIN playlist_tracks pt ON pt.track_id = t.id
            WHERE pt.playlist_id = ?
            ORDER BY pt.position
            """,
            (playlist_id,),
        )

        tracks = [
            Track(
                id=r["id"],
                video_id=r["video_id"],
                title=r["title"],
                channel=r["channel"],
                duration=r["duration"],
                thumbnail_url=r["thumbnail_url"],
            )
            for r in cursor.fetchall()
        ]

        return Playlist(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            tracks=tracks,
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
        )

    def get_playlist_by_name(self, name: str) -> Optional[Playlist]:
        """Get a playlist by name."""
        cursor = self._conn.execute(
            "SELECT id FROM playlists WHERE name = ?",
            (name,),
        )
        row = cursor.fetchone()

        if row:
            return self.get_playlist(row["id"])
        return None

    def get_all_playlists(self) -> list[Playlist]:
        """Get all playlists (without tracks for efficiency)."""
        cursor = self._conn.execute(
            """
            SELECT p.*, COUNT(pt.id) as track_count
            FROM playlists p
            LEFT JOIN playlist_tracks pt ON pt.playlist_id = p.id
            GROUP BY p.id
            ORDER BY p.updated_at DESC
            """
        )

        playlists = []
        for row in cursor.fetchall():
            playlists.append(
                Playlist(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    tracks=[],  # Not loaded for efficiency
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                    updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
                )
            )

        return playlists

    def update_playlist(self, playlist_id: int, name: str = None, description: str = None) -> bool:
        """Update playlist metadata."""
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if not updates:
            return False

        updates.append("updated_at = ?")
        params.append(datetime.now())
        params.append(playlist_id)

        cursor = self._conn.execute(
            f"UPDATE playlists SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        self._conn.commit()

        return cursor.rowcount > 0

    def delete_playlist(self, playlist_id: int) -> bool:
        """Delete a playlist."""
        cursor = self._conn.execute(
            "DELETE FROM playlists WHERE id = ?",
            (playlist_id,),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def add_track_to_playlist(self, playlist_id: int, track: Track) -> bool:
        """Add a track to a playlist."""
        # Get current max position
        cursor = self._conn.execute(
            "SELECT MAX(position) FROM playlist_tracks WHERE playlist_id = ?",
            (playlist_id,),
        )
        max_pos = cursor.fetchone()[0] or 0

        try:
            self._conn.execute(
                """
                INSERT INTO playlist_tracks (playlist_id, track_id, position)
                VALUES (?, ?, ?)
                """,
                (playlist_id, track.id, max_pos + 1),
            )
            self._conn.execute(
                "UPDATE playlists SET updated_at = ? WHERE id = ?",
                (datetime.now(), playlist_id),
            )
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Already exists

    def remove_track_from_playlist(self, playlist_id: int, track_id: int) -> bool:
        """Remove a track from a playlist."""
        cursor = self._conn.execute(
            """
            DELETE FROM playlist_tracks
            WHERE playlist_id = ? AND track_id = ?
            """,
            (playlist_id, track_id),
        )
        if cursor.rowcount > 0:
            self._conn.execute(
                "UPDATE playlists SET updated_at = ? WHERE id = ?",
                (datetime.now(), playlist_id),
            )
            self._conn.commit()
            return True
        return False

    # ==================== History Operations ====================

    def add_to_history(self, track: Track) -> HistoryEntry:
        """Add or update a history entry for a track."""
        now = datetime.now()

        # Check if already in history
        cursor = self._conn.execute(
            "SELECT * FROM history WHERE track_id = ?",
            (track.id,),
        )
        row = cursor.fetchone()

        if row:
            # Update existing
            self._conn.execute(
                """
                UPDATE history
                SET played_at = ?, play_count = play_count + 1
                WHERE id = ?
                """,
                (now, row["id"]),
            )
            self._conn.commit()

            return HistoryEntry(
                id=row["id"],
                track=track,
                played_at=now,
                play_count=row["play_count"] + 1,
                last_position=row["last_position"],
                completed=bool(row["completed"]),
            )
        else:
            # Create new
            cursor = self._conn.execute(
                """
                INSERT INTO history (track_id, played_at)
                VALUES (?, ?)
                """,
                (track.id, now),
            )
            self._conn.commit()

            return HistoryEntry(
                id=cursor.lastrowid,
                track=track,
                played_at=now,
                play_count=1,
            )

    def update_history_position(self, track_id: int, position: int, completed: bool = False) -> None:
        """Update the last position for a track in history."""
        self._conn.execute(
            """
            UPDATE history
            SET last_position = ?, completed = ?
            WHERE track_id = ?
            """,
            (position, int(completed), track_id),
        )
        self._conn.commit()

    def get_history(self, limit: int = 50, offset: int = 0) -> list[HistoryEntry]:
        """Get play history."""
        cursor = self._conn.execute(
            """
            SELECT h.*, t.video_id, t.title, t.channel, t.duration, t.thumbnail_url
            FROM history h
            JOIN tracks t ON t.id = h.track_id
            ORDER BY h.played_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )

        entries = []
        for row in cursor.fetchall():
            track = Track(
                id=row["track_id"],
                video_id=row["video_id"],
                title=row["title"],
                channel=row["channel"],
                duration=row["duration"],
                thumbnail_url=row["thumbnail_url"],
            )
            entries.append(
                HistoryEntry(
                    id=row["id"],
                    track=track,
                    played_at=datetime.fromisoformat(row["played_at"]),
                    play_count=row["play_count"],
                    last_position=row["last_position"],
                    completed=bool(row["completed"]),
                )
            )

        return entries

    def clear_history(self) -> int:
        """Clear all history. Returns count deleted."""
        cursor = self._conn.execute("DELETE FROM history")
        self._conn.commit()
        return cursor.rowcount

    def get_most_played(self, limit: int = 10) -> list[HistoryEntry]:
        """Get most played tracks."""
        cursor = self._conn.execute(
            """
            SELECT h.*, t.video_id, t.title, t.channel, t.duration, t.thumbnail_url
            FROM history h
            JOIN tracks t ON t.id = h.track_id
            ORDER BY h.play_count DESC
            LIMIT ?
            """,
            (limit,),
        )

        entries = []
        for row in cursor.fetchall():
            track = Track(
                id=row["track_id"],
                video_id=row["video_id"],
                title=row["title"],
                channel=row["channel"],
                duration=row["duration"],
                thumbnail_url=row["thumbnail_url"],
            )
            entries.append(
                HistoryEntry(
                    id=row["id"],
                    track=track,
                    played_at=datetime.fromisoformat(row["played_at"]),
                    play_count=row["play_count"],
                    last_position=row["last_position"],
                    completed=bool(row["completed"]),
                )
            )

        return entries

    # ==================== Queue Persistence ====================

    def save_queue(
        self,
        items: list[dict],
        current_index: int,
        shuffle_mode: bool,
        repeat_mode: str,
    ) -> None:
        """
        Save the current queue to database.

        Args:
            items: List of dicts with video_id, title, channel, duration, playback_position
            current_index: Current playing index
            shuffle_mode: Whether shuffle is enabled
            repeat_mode: 'none', 'one', or 'all'
        """
        # Clear existing queue
        self._conn.execute("DELETE FROM queue")

        # Save each item
        for position, item in enumerate(items):
            # Get or create track
            track = self.get_or_create_track(
                video_id=item["video_id"],
                title=item["title"],
                channel=item["channel"],
                duration=item["duration"],
            )

            self._conn.execute(
                """
                INSERT INTO queue (track_id, position, playback_position)
                VALUES (?, ?, ?)
                """,
                (track.id, position, item.get("playback_position", 0)),
            )

        # Save queue state
        self._conn.execute(
            """
            UPDATE queue_state SET
                current_index = ?,
                shuffle_mode = ?,
                repeat_mode = ?,
                updated_at = ?
            WHERE id = 1
            """,
            (current_index, int(shuffle_mode), repeat_mode, datetime.now()),
        )

        self._conn.commit()

    def load_queue(self) -> tuple[list[dict], int, bool, str]:
        """
        Load the saved queue from database.

        Returns:
            Tuple of (items, current_index, shuffle_mode, repeat_mode)
            items is a list of dicts with video_id, title, channel, duration, playback_position
        """
        items = []

        # Load queue items
        cursor = self._conn.execute(
            """
            SELECT q.position, q.playback_position, t.video_id, t.title, t.channel, t.duration
            FROM queue q
            JOIN tracks t ON t.id = q.track_id
            ORDER BY q.position
            """
        )

        for row in cursor.fetchall():
            items.append({
                "video_id": row["video_id"],
                "title": row["title"],
                "channel": row["channel"],
                "duration": row["duration"],
                "playback_position": row["playback_position"],
            })

        # Load queue state
        cursor = self._conn.execute(
            "SELECT current_index, shuffle_mode, repeat_mode FROM queue_state WHERE id = 1"
        )
        row = cursor.fetchone()

        if row:
            current_index = row["current_index"]
            shuffle_mode = bool(row["shuffle_mode"])
            repeat_mode = row["repeat_mode"]
        else:
            current_index = -1
            shuffle_mode = False
            repeat_mode = "none"

        return items, current_index, shuffle_mode, repeat_mode

    def update_queue_item_position(self, video_id: str, playback_position: int) -> None:
        """Update the playback position for a queue item."""
        self._conn.execute(
            """
            UPDATE queue SET playback_position = ?
            WHERE track_id = (SELECT id FROM tracks WHERE video_id = ?)
            """,
            (playback_position, video_id),
        )
        self._conn.commit()

    def clear_queue(self) -> None:
        """Clear the saved queue."""
        self._conn.execute("DELETE FROM queue")
        self._conn.execute(
            "UPDATE queue_state SET current_index = -1, updated_at = ? WHERE id = 1",
            (datetime.now(),),
        )
        self._conn.commit()
