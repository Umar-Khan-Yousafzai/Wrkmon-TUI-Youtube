"""Tests for the lyrics module."""

import pytest
from wrkmon.core.lyrics import _clean_query, _split_artist_title, LyricsFetcher


class TestCleanQuery:
    """Tests for the _clean_query helper."""

    def test_removes_official_video(self):
        assert "Artist - Song" == _clean_query("Artist - Song (Official Video)")

    def test_removes_official_music_video(self):
        result = _clean_query("Artist - Song (Official Music Video)")
        assert "Official" not in result

    def test_removes_audio_tag(self):
        result = _clean_query("Artist - Song [Official Audio]")
        assert "Audio" not in result

    def test_removes_lyrics_tag(self):
        result = _clean_query("Artist - Song (Lyrics)")
        assert "Lyrics" not in result

    def test_removes_hd_tags(self):
        result = _clean_query("Artist - Song [HD] [4K]")
        assert "HD" not in result
        assert "4K" not in result

    def test_removes_pipe_and_after(self):
        result = _clean_query("Artist - Song | Official Channel")
        assert "|" not in result
        assert "Channel" not in result

    def test_removes_hashtags(self):
        result = _clean_query("Artist - Song #newmusic #2024")
        assert "#" not in result

    def test_preserves_normal_text(self):
        assert "Artist - Song" == _clean_query("Artist - Song")

    def test_collapses_whitespace(self):
        result = _clean_query("Artist  -  Song   (Official Video)")
        assert "  " not in result

    def test_strips_trailing_dash(self):
        result = _clean_query("Artist - Song -")
        assert not result.endswith("-")


class TestSplitArtistTitle:
    """Tests for _split_artist_title helper."""

    def test_splits_on_dash(self):
        artist, title = _split_artist_title("Coldplay - Yellow")
        assert artist == "Coldplay"
        assert title == "Yellow"

    def test_no_dash(self):
        artist, title = _split_artist_title("Just a title")
        assert artist == ""
        assert title == "Just a title"

    def test_multiple_dashes(self):
        artist, title = _split_artist_title("A-ha - Take On Me - Remastered")
        assert artist == "A-ha"
        assert title == "Take On Me - Remastered"


class TestLyricsFetcher:
    """Tests for LyricsFetcher (cache behavior only, no HTTP calls)."""

    def test_cache_starts_empty(self):
        fetcher = LyricsFetcher()
        assert len(fetcher._cache) == 0

    def test_clear_cache(self):
        fetcher = LyricsFetcher()
        fetcher._cache["test"] = "lyrics"
        fetcher.clear_cache()
        assert len(fetcher._cache) == 0

    @pytest.mark.asyncio
    async def test_empty_title_returns_none(self):
        fetcher = LyricsFetcher()
        result = await fetcher.fetch("")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_hit(self):
        fetcher = LyricsFetcher()
        # Pre-populate cache
        fetcher._cache["coldplay - yellow"] = "Look at the stars..."
        result = await fetcher.fetch("Coldplay - Yellow")
        assert result == "Look at the stars..."
