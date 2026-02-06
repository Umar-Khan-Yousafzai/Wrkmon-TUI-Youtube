"""YouTube integration using yt-dlp."""

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Optional
import yt_dlp

logger = logging.getLogger("wrkmon.youtube")


@dataclass
class SearchResult:
    """Represents a YouTube search result."""

    video_id: str
    title: str
    channel: str
    duration: int  # seconds
    view_count: int
    thumbnail_url: Optional[str] = None

    @property
    def url(self) -> str:
        """Get the YouTube URL for this result."""
        return f"https://www.youtube.com/watch?v={self.video_id}"

    @property
    def duration_str(self) -> str:
        """Get duration as formatted string."""
        total_secs = int(self.duration)
        mins, secs = divmod(total_secs, 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            return f"{hours}:{mins:02d}:{secs:02d}"
        return f"{mins}:{secs:02d}"


@dataclass
class StreamInfo:
    """Represents extracted stream information."""

    video_id: str
    title: str
    audio_url: str
    duration: int
    channel: str
    thumbnail_url: Optional[str] = None


class YouTubeClient:
    """Client for searching and extracting YouTube content."""

    def __init__(self):
        self._search_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "default_search": "ytsearch",
        }
        self._extract_opts = {
            "quiet": True,
            "no_warnings": True,
            "format": "bestaudio/best",
            "noplaylist": True,
        }

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """Search YouTube for videos."""
        return await asyncio.to_thread(self._search_sync, query, max_results)

    def _search_sync(self, query: str, max_results: int) -> list[SearchResult]:
        """Synchronous search implementation."""
        results = []
        opts = {
            **self._search_opts,
            "playlistend": max_results,
        }

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                search_query = f"ytsearch{max_results}:{query}"
                info = ydl.extract_info(search_query, download=False)

                if info and "entries" in info:
                    for entry in info["entries"]:
                        if entry is None:
                            continue
                        result = SearchResult(
                            video_id=entry.get("id", ""),
                            title=entry.get("title", "Unknown"),
                            channel=entry.get("channel", entry.get("uploader", "Unknown")),
                            duration=entry.get("duration", 0) or 0,
                            view_count=entry.get("view_count", 0) or 0,
                            thumbnail_url=entry.get("thumbnail"),
                        )
                        results.append(result)
        except Exception as e:
            logger.error(f"Search failed for '{query}': {e}")

        return results

    async def get_stream_url(self, video_id: str) -> Optional[StreamInfo]:
        """Extract the audio stream URL for a video."""
        return await asyncio.to_thread(self._get_stream_sync, video_id)

    def _get_stream_sync(self, video_id: str) -> Optional[StreamInfo]:
        """Synchronous stream extraction with retry."""
        url = f"https://www.youtube.com/watch?v={video_id}"
        max_retries = 3

        for attempt in range(max_retries):
            try:
                return self._extract_stream(url, video_id)
            except Exception as e:
                logger.warning(f"Stream extraction attempt {attempt + 1}/{max_retries} failed for {video_id}: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(1.0 * (attempt + 1))  # Backoff
        logger.error(f"All {max_retries} attempts failed for {video_id}")
        return None

    def _extract_stream(self, url: str, video_id: str) -> Optional[StreamInfo]:
        """Single attempt at stream extraction."""
        try:
            with yt_dlp.YoutubeDL(self._extract_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if info is None:
                    return None

                # Get the best audio URL
                audio_url = info.get("url")

                # If formats are available, find best audio
                if not audio_url and "formats" in info:
                    formats = info["formats"]
                    # Prefer audio-only formats
                    audio_formats = [
                        f for f in formats if f.get("acodec") != "none" and f.get("vcodec") == "none"
                    ]
                    if audio_formats:
                        # Sort by quality (abr = audio bitrate)
                        audio_formats.sort(key=lambda x: x.get("abr", 0) or 0, reverse=True)
                        audio_url = audio_formats[0].get("url")
                    elif formats:
                        # Fallback to any format with audio
                        for f in formats:
                            if f.get("acodec") != "none":
                                audio_url = f.get("url")
                                break

                if not audio_url:
                    return None

                return StreamInfo(
                    video_id=video_id,
                    title=info.get("title", "Unknown"),
                    audio_url=audio_url,
                    duration=info.get("duration", 0) or 0,
                    channel=info.get("channel", info.get("uploader", "Unknown")),
                    thumbnail_url=info.get("thumbnail"),
                )
        except Exception as e:
            logger.error(f"Stream extraction error for {video_id}: {e}")
            return None

    async def extract_playlist(self, playlist_url: str, max_results: int = 50) -> list[SearchResult]:
        """Extract tracks from a YouTube playlist URL."""
        return await asyncio.to_thread(self._extract_playlist_sync, playlist_url, max_results)

    def _extract_playlist_sync(self, playlist_url: str, max_results: int) -> list[SearchResult]:
        """Synchronous playlist extraction."""
        results = []
        opts = {
            **self._search_opts,
            "playlistend": max_results,
            "extract_flat": True,
        }

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(playlist_url, download=False)

                if info and "entries" in info:
                    for entry in info["entries"][:max_results]:
                        if entry is None:
                            continue
                        result = SearchResult(
                            video_id=entry.get("id", ""),
                            title=entry.get("title", "Unknown"),
                            channel=entry.get("channel", entry.get("uploader", "Unknown")),
                            duration=entry.get("duration", 0) or 0,
                            view_count=entry.get("view_count", 0) or 0,
                            thumbnail_url=entry.get("thumbnail"),
                        )
                        if result.video_id:
                            results.append(result)
        except Exception as e:
            logger.error(f"Playlist extraction failed for {playlist_url}: {e}")

        return results

    @staticmethod
    def is_playlist_url(url: str) -> bool:
        """Check if a URL is a YouTube playlist."""
        return bool(re.search(r"[?&]list=", url))

    @staticmethod
    def is_youtube_url(url: str) -> bool:
        """Check if a string is a YouTube URL."""
        return bool(re.search(r"(youtube\.com|youtu\.be)", url))

    async def get_video_info(self, video_id: str) -> Optional[SearchResult]:
        """Get video metadata without extracting stream URL."""
        return await asyncio.to_thread(self._get_info_sync, video_id)

    def _get_info_sync(self, video_id: str) -> Optional[SearchResult]:
        """Synchronous video info extraction."""
        url = f"https://www.youtube.com/watch?v={video_id}"
        opts = {
            **self._search_opts,
            "extract_flat": False,
        }

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if info is None:
                    return None

                return SearchResult(
                    video_id=video_id,
                    title=info.get("title", "Unknown"),
                    channel=info.get("channel", info.get("uploader", "Unknown")),
                    duration=info.get("duration", 0) or 0,
                    view_count=info.get("view_count", 0) or 0,
                    thumbnail_url=info.get("thumbnail"),
                )
        except Exception as e:
            logger.error(f"Video info fetch failed for {video_id}: {e}")
            return None

    async def get_trending_music(self, max_results: int = 10) -> list[SearchResult]:
        """Get trending/popular music videos."""
        return await asyncio.to_thread(self._get_trending_sync, max_results)

    def _get_trending_sync(self, max_results: int) -> list[SearchResult]:
        """Fetch trending music from YouTube Music charts or popular searches."""
        results = []

        # Try to get from YouTube Music trending/charts
        trending_queries = [
            "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",  # Popular Music
            "https://www.youtube.com/playlist?list=PL4fGSI1pDJn6puJdseH2Rt9sMvt9E2M4i",  # Trending Music
        ]

        opts = {
            **self._search_opts,
            "playlistend": max_results,
            "extract_flat": True,
        }

        # Try playlist first
        for playlist_url in trending_queries:
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(playlist_url, download=False)

                    if info and "entries" in info:
                        for entry in info["entries"][:max_results]:
                            if entry is None:
                                continue
                            result = SearchResult(
                                video_id=entry.get("id", ""),
                                title=entry.get("title", "Unknown"),
                                channel=entry.get("channel", entry.get("uploader", "Unknown")),
                                duration=entry.get("duration", 0) or 0,
                                view_count=entry.get("view_count", 0) or 0,
                                thumbnail_url=entry.get("thumbnail"),
                            )
                            if result.video_id:
                                results.append(result)

                        if results:
                            return results[:max_results]
            except Exception:
                continue

        # Fallback: search for popular music
        fallback_searches = [
            "popular music 2024",
            "trending songs",
            "top hits music",
        ]

        for query in fallback_searches:
            try:
                search_results = self._search_sync(query, max_results)
                if search_results:
                    return search_results
            except Exception:
                continue

        return results

    async def get_recommendations(self, video_id: str, max_results: int = 5) -> list[SearchResult]:
        """Get recommended videos based on a video (related videos)."""
        return await asyncio.to_thread(self._get_recommendations_sync, video_id, max_results)

    def _get_recommendations_sync(self, video_id: str, max_results: int) -> list[SearchResult]:
        """Get related/recommended videos."""
        results = []
        url = f"https://www.youtube.com/watch?v={video_id}"

        opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "noplaylist": True,
        }

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if info and "related_videos" in info:
                    for entry in info["related_videos"][:max_results]:
                        if entry is None:
                            continue
                        result = SearchResult(
                            video_id=entry.get("id", ""),
                            title=entry.get("title", "Unknown"),
                            channel=entry.get("channel", entry.get("uploader", "Unknown")),
                            duration=entry.get("duration", 0) or 0,
                            view_count=entry.get("view_count", 0) or 0,
                            thumbnail_url=entry.get("thumbnail"),
                        )
                        if result.video_id:
                            results.append(result)
        except Exception as e:
            logger.error(f"Recommendations failed for {video_id}: {e}")

        return results
