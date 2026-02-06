"""Lyrics fetcher module using the lyrics.ovh free API."""

import asyncio
import re
import logging
import urllib.parse
from typing import Optional

logger = logging.getLogger("wrkmon.lyrics")

_CLEAN_PATTERNS = [
    re.compile(r"\(Official\s+Music\s+Video\)", re.IGNORECASE),
    re.compile(r"\(Official\s+Video\)", re.IGNORECASE),
    re.compile(r"\(Official\s+Audio\)", re.IGNORECASE),
    re.compile(r"\(Official\s+Lyric\s+Video\)", re.IGNORECASE),
    re.compile(r"\(Lyric\s+Video\)", re.IGNORECASE),
    re.compile(r"\(Lyrics\)", re.IGNORECASE),
    re.compile(r"\(Audio\)", re.IGNORECASE),
    re.compile(r"\(Live\)", re.IGNORECASE),
    re.compile(r"\(Visualizer\)", re.IGNORECASE),
    re.compile(r"\[Official\s+Music\s+Video\]", re.IGNORECASE),
    re.compile(r"\[Official\s+Video\]", re.IGNORECASE),
    re.compile(r"\[Official\s+Audio\]", re.IGNORECASE),
    re.compile(r"\[Lyric\s+Video\]", re.IGNORECASE),
    re.compile(r"\[Lyrics\]", re.IGNORECASE),
    re.compile(r"\[Audio\]", re.IGNORECASE),
    re.compile(r"\[HD\]", re.IGNORECASE),
    re.compile(r"\[HQ\]", re.IGNORECASE),
    re.compile(r"\[4K\]", re.IGNORECASE),
    re.compile(r"\(HD\)", re.IGNORECASE),
    re.compile(r"\(HQ\)", re.IGNORECASE),
    re.compile(r"\(4K\)", re.IGNORECASE),
    re.compile(r"\bft\.\s*[^(\[]*", re.IGNORECASE),
    re.compile(r"\bfeat\.\s*[^(\[]*", re.IGNORECASE),
    re.compile(r"\|.*$"),
    re.compile(r"#\w+"),
]

_BASE_URL = "https://api.lyrics.ovh/v1"
_MAX_RETRIES = 3
_INITIAL_BACKOFF = 1.0
_REQUEST_TIMEOUT = 10


def _clean_query(query: str) -> str:
    """Remove common YouTube suffixes from a search query."""
    cleaned = query
    for pattern in _CLEAN_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    cleaned = re.sub(r"\s*-\s*$", "", cleaned)
    return cleaned


def _split_artist_title(query: str) -> tuple[str, str]:
    """Split a cleaned query into (artist, title)."""
    if " - " in query:
        artist, title = query.split(" - ", maxsplit=1)
        return artist.strip(), title.strip()
    return "", query.strip()


def _fetch_lyrics_sync(artist: str, title: str) -> Optional[str]:
    """Blocking HTTP GET against lyrics.ovh."""
    import urllib.request
    import json

    safe_artist = urllib.parse.quote(artist, safe="")
    safe_title = urllib.parse.quote(title, safe="")
    url = f"{_BASE_URL}/{safe_artist}/{safe_title}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "wrkmon/1.2"})
        with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT) as response:
            if response.status == 404:
                return None
            data = json.loads(response.read().decode())
            lyrics = data.get("lyrics")
            if not lyrics or not lyrics.strip():
                return None
            return lyrics.strip()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except Exception:
        raise


class LyricsFetcher:
    """Async lyrics fetcher with caching and retries."""

    def __init__(self) -> None:
        self._cache: dict[str, Optional[str]] = {}

    async def fetch(self, query: str) -> Optional[str]:
        """Fetch lyrics for a query (typically a YouTube video title)."""
        cleaned = _clean_query(query)
        cache_key = cleaned.lower()

        if cache_key in self._cache:
            return self._cache[cache_key]

        artist, title = _split_artist_title(cleaned)

        if not title:
            self._cache[cache_key] = None
            return None

        lyrics = await self._fetch_with_retry(artist, title)
        self._cache[cache_key] = lyrics
        return lyrics

    def clear_cache(self) -> None:
        """Drop all cached lyrics."""
        self._cache.clear()

    async def _fetch_with_retry(self, artist: str, title: str) -> Optional[str]:
        """Fetch with exponential backoff retries."""
        backoff = _INITIAL_BACKOFF

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                return await asyncio.to_thread(_fetch_lyrics_sync, artist, title)
            except Exception as exc:
                # Don't retry 404s
                if hasattr(exc, 'code') and exc.code == 404:
                    return None
                logger.warning(
                    "Lyrics attempt %d/%d failed for %s - %s: %s",
                    attempt, _MAX_RETRIES, artist, title, exc,
                )
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(backoff)
                    backoff *= 2

        return None
