"""Database migrations for wrkmon."""

import sqlite3
from typing import Callable

# List of migrations in order
# Each migration is a tuple of (version, description, up_sql)
MIGRATIONS: list[tuple[int, str, str]] = [
    (
        1,
        "Initial schema",
        """
        -- Tracks table
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            channel TEXT NOT NULL,
            duration INTEGER NOT NULL,
            thumbnail_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_tracks_video_id ON tracks(video_id);

        -- Playlists table
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Playlist tracks junction table
        CREATE TABLE IF NOT EXISTS playlist_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id INTEGER NOT NULL,
            track_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
            FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
            UNIQUE(playlist_id, track_id)
        );
        CREATE INDEX IF NOT EXISTS idx_playlist_tracks_playlist ON playlist_tracks(playlist_id);

        -- History table
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER NOT NULL,
            played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            play_count INTEGER DEFAULT 1,
            last_position INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_history_played_at ON history(played_at DESC);
        CREATE INDEX IF NOT EXISTS idx_history_track ON history(track_id);

        -- Schema version table
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
    ),
    (
        2,
        "Add queue persistence",
        """
        -- Queue table for persistent queue
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            playback_position INTEGER DEFAULT 0,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_queue_position ON queue(position);

        -- Queue state table (single row for current state)
        CREATE TABLE IF NOT EXISTS queue_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            current_index INTEGER DEFAULT -1,
            shuffle_mode INTEGER DEFAULT 0,
            repeat_mode TEXT DEFAULT 'none',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        INSERT OR IGNORE INTO queue_state (id) VALUES (1);
        """,
    ),
]


class MigrationManager:
    """Manages database migrations."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._ensure_version_table()

    def _ensure_version_table(self) -> None:
        """Ensure schema_version table exists."""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._conn.commit()

    def get_current_version(self) -> int:
        """Get the current schema version."""
        cursor = self._conn.execute(
            "SELECT MAX(version) FROM schema_version"
        )
        result = cursor.fetchone()[0]
        return result if result is not None else 0

    def get_pending_migrations(self) -> list[tuple[int, str, str]]:
        """Get list of pending migrations."""
        current = self.get_current_version()
        return [m for m in MIGRATIONS if m[0] > current]

    def apply_migration(self, version: int, description: str, sql: str) -> None:
        """Apply a single migration."""
        # Execute migration SQL
        self._conn.executescript(sql)

        # Record the migration
        self._conn.execute(
            "INSERT INTO schema_version (version) VALUES (?)",
            (version,),
        )
        self._conn.commit()

    def migrate(self, target_version: int | None = None) -> list[int]:
        """Run pending migrations up to target version. Returns applied versions."""
        applied = []
        pending = self.get_pending_migrations()

        for version, description, sql in pending:
            if target_version is not None and version > target_version:
                break

            self.apply_migration(version, description, sql)
            applied.append(version)

        return applied

    def needs_migration(self) -> bool:
        """Check if there are pending migrations."""
        return len(self.get_pending_migrations()) > 0


def run_migrations(conn: sqlite3.Connection) -> list[int]:
    """Convenience function to run all pending migrations."""
    manager = MigrationManager(conn)
    return manager.migrate()
