"""Tests for the Downloader module (unit tests only, no actual downloads)."""

import pytest
from pathlib import Path
from wrkmon.core.downloader import _sanitize_filename, Downloader


class TestSanitizeFilename:
    """Tests for _sanitize_filename."""

    def test_basic_name(self):
        assert _sanitize_filename("hello world") == "hello world"

    def test_removes_forbidden_chars(self):
        result = _sanitize_filename('file:name*with?"bad<chars>|')
        assert ":" not in result
        assert "*" not in result
        assert "?" not in result
        assert '"' not in result
        assert "<" not in result
        assert ">" not in result
        assert "|" not in result

    def test_collapses_whitespace(self):
        result = _sanitize_filename("too   many    spaces")
        assert result == "too many spaces"

    def test_truncates_long_names(self):
        result = _sanitize_filename("A" * 300, max_length=100)
        assert len(result) <= 100

    def test_empty_name_fallback(self):
        result = _sanitize_filename("***")
        assert result == "untitled"

    def test_strips_trailing_dots(self):
        result = _sanitize_filename("filename...")
        assert not result.endswith(".")

    def test_unicode_normalization(self):
        # Should not crash on unicode
        result = _sanitize_filename("caf\u00e9 music \u2013 relax")
        assert len(result) > 0


class TestDownloader:
    """Tests for Downloader class (no network calls)."""

    def test_init_creates_directory(self, tmp_path):
        dl_dir = tmp_path / "downloads"
        downloader = Downloader(download_dir=dl_dir)
        assert dl_dir.exists()
        assert downloader.download_dir == dl_dir

    def test_get_local_path_none(self, tmp_path):
        downloader = Downloader(download_dir=tmp_path)
        assert downloader.get_local_path("nonexistent") is None

    def test_get_local_path_finds_file(self, tmp_path):
        downloader = Downloader(download_dir=tmp_path)
        # Create a fake downloaded file
        fake_file = tmp_path / "Song Title [abc123].mp3"
        fake_file.write_text("fake audio")
        result = downloader.get_local_path("abc123")
        assert result == fake_file

    def test_get_local_path_prefers_mp3(self, tmp_path):
        downloader = Downloader(download_dir=tmp_path)
        # Create both mp3 and webm
        (tmp_path / "Song [abc123].webm").write_text("webm")
        mp3 = tmp_path / "Song [abc123].mp3"
        mp3.write_text("mp3")
        result = downloader.get_local_path("abc123")
        assert result == mp3

    @pytest.mark.asyncio
    async def test_is_downloaded_false(self, tmp_path):
        downloader = Downloader(download_dir=tmp_path)
        assert not await downloader.is_downloaded("nonexistent")

    @pytest.mark.asyncio
    async def test_is_downloaded_true(self, tmp_path):
        downloader = Downloader(download_dir=tmp_path)
        (tmp_path / "Song [abc123].mp3").write_text("fake")
        assert await downloader.is_downloaded("abc123")

    @pytest.mark.asyncio
    async def test_download_returns_existing(self, tmp_path):
        downloader = Downloader(download_dir=tmp_path)
        existing = tmp_path / "Song [abc123].mp3"
        existing.write_text("fake audio data")
        result = await downloader.download("abc123", "Song")
        assert result == existing

    def test_build_output_template(self, tmp_path):
        downloader = Downloader(download_dir=tmp_path)
        template = downloader._build_output_template("vid123", "My Song")
        assert "vid123" in template
        assert "My Song" in template
        assert template.endswith(".%(ext)s")
