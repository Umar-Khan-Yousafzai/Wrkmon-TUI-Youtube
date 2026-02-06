"""Tests for the database migration system."""

import sqlite3
import pytest
from wrkmon.data.migrations import MigrationManager, MIGRATIONS, run_migrations


@pytest.fixture
def db_conn():
    """Create an in-memory SQLite connection."""
    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()


class TestMigrationManager:
    """Tests for MigrationManager."""

    def test_initial_version_is_zero(self, db_conn):
        mgr = MigrationManager(db_conn)
        assert mgr.get_current_version() == 0

    def test_needs_migration_initially(self, db_conn):
        mgr = MigrationManager(db_conn)
        assert mgr.needs_migration()

    def test_apply_single_migration(self, db_conn):
        mgr = MigrationManager(db_conn)
        version, desc, sql = MIGRATIONS[0]
        mgr.apply_migration(version, desc, sql)
        assert mgr.get_current_version() == 1

    def test_migrate_all(self, db_conn):
        mgr = MigrationManager(db_conn)
        applied = mgr.migrate()
        assert len(applied) == len(MIGRATIONS)
        assert mgr.get_current_version() == MIGRATIONS[-1][0]
        assert not mgr.needs_migration()

    def test_migrate_target_version(self, db_conn):
        mgr = MigrationManager(db_conn)
        applied = mgr.migrate(target_version=1)
        assert applied == [1]
        assert mgr.get_current_version() == 1
        assert mgr.needs_migration()

    def test_migrate_idempotent(self, db_conn):
        mgr = MigrationManager(db_conn)
        mgr.migrate()
        applied = mgr.migrate()
        assert len(applied) == 0  # Nothing new to apply

    def test_pending_migrations(self, db_conn):
        mgr = MigrationManager(db_conn)
        pending = mgr.get_pending_migrations()
        assert len(pending) == len(MIGRATIONS)
        mgr.migrate(target_version=1)
        pending = mgr.get_pending_migrations()
        assert len(pending) == len(MIGRATIONS) - 1

    def test_run_migrations_convenience(self, db_conn):
        applied = run_migrations(db_conn)
        assert len(applied) == len(MIGRATIONS)

    def test_tables_created_after_migration(self, db_conn):
        run_migrations(db_conn)
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = {row[0] for row in cursor.fetchall()}
        expected = {
            "tracks", "playlists", "playlist_tracks", "history",
            "schema_version", "queue", "queue_state",
            "search_history", "downloads",
        }
        assert expected.issubset(tables)
