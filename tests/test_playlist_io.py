"""Tests for playlist import/export module."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from wrkmon.core.playlist_io import (
    export_playlist,
    import_playlist,
    _extract_video_id,
)


@pytest.fixture
def mock_playlist():
    """Create a mock Playlist object."""
    playlist = MagicMock()
    playlist.name = "Test Playlist"
    playlist.description = "A test playlist"
    playlist.track_count = 2
    playlist.total_duration = 360

    track1 = MagicMock()
    track1.video_id = "abc123"
    track1.title = "Track One"
    track1.channel = "Channel A"
    track1.duration = 180
    track1.url = "https://www.youtube.com/watch?v=abc123"

    track2 = MagicMock()
    track2.video_id = "def456"
    track2.title = "Track Two"
    track2.channel = "Channel B"
    track2.duration = 180
    track2.url = "https://www.youtube.com/watch?v=def456"

    playlist.tracks = [track1, track2]
    return playlist


class TestExportPlaylist:
    """Tests for export_playlist."""

    def test_export_json(self, mock_playlist, tmp_path):
        filepath = tmp_path / "test.json"
        result = export_playlist(mock_playlist, filepath, format="json")
        assert result is True
        assert filepath.exists()

        data = json.loads(filepath.read_text())
        assert data["name"] == "Test Playlist"
        assert len(data["tracks"]) == 2
        assert data["tracks"][0]["video_id"] == "abc123"

    def test_export_m3u(self, mock_playlist, tmp_path):
        filepath = tmp_path / "test.m3u"
        result = export_playlist(mock_playlist, filepath, format="m3u")
        assert result is True
        assert filepath.exists()

        content = filepath.read_text()
        assert "#EXTM3U" in content
        assert "#PLAYLIST:Test Playlist" in content
        assert "https://www.youtube.com/watch?v=abc123" in content

    def test_export_unknown_format(self, mock_playlist, tmp_path):
        filepath = tmp_path / "test.xyz"
        result = export_playlist(mock_playlist, filepath, format="xyz")
        assert result is False

    def test_export_creates_parent_dirs(self, mock_playlist, tmp_path):
        filepath = tmp_path / "sub" / "dir" / "test.json"
        result = export_playlist(mock_playlist, filepath, format="json")
        assert result is True
        assert filepath.exists()


class TestImportPlaylist:
    """Tests for import_playlist."""

    def test_import_json(self, tmp_path):
        data = {
            "name": "Imported",
            "description": "Test import",
            "tracks": [
                {"video_id": "abc123", "title": "Track", "channel": "Ch", "duration": 120}
            ],
        }
        filepath = tmp_path / "test.json"
        filepath.write_text(json.dumps(data))

        result = import_playlist(filepath)
        assert result is not None
        assert result["name"] == "Imported"
        assert len(result["tracks"]) == 1

    def test_import_json_missing_tracks(self, tmp_path):
        filepath = tmp_path / "test.json"
        filepath.write_text(json.dumps({"name": "Bad"}))
        result = import_playlist(filepath)
        assert result is None

    def test_import_m3u(self, tmp_path):
        content = (
            "#EXTM3U\n"
            "#PLAYLIST:My Playlist\n"
            "#EXTINF:180,Track One - Channel A\n"
            "https://www.youtube.com/watch?v=abc12345678\n"
        )
        filepath = tmp_path / "test.m3u"
        filepath.write_text(content)

        result = import_playlist(filepath)
        assert result is not None
        assert result["name"] == "My Playlist"
        assert len(result["tracks"]) == 1
        assert result["tracks"][0]["video_id"] == "abc12345678"

    def test_import_unknown_format(self, tmp_path):
        filepath = tmp_path / "test.xyz"
        filepath.write_text("stuff")
        result = import_playlist(filepath)
        assert result is None


class TestExtractVideoId:
    """Tests for _extract_video_id."""

    def test_standard_url(self):
        assert _extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_short_url(self):
        assert _extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_no_match(self):
        assert _extract_video_id("https://example.com/page") is None

    def test_embedded_url(self):
        result = _extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ")
        assert result == "dQw4w9WgXcQ"
