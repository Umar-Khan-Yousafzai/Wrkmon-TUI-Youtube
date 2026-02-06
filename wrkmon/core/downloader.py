"""Download manager for saving audio files locally using yt-dlp."""

import asyncio
import logging
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import yt_dlp

from wrkmon.utils.config import get_config

logger = logging.getLogger("wrkmon.downloader")

# Type alias for the progress callback.
# Called with (video_id, status, percent, speed, eta) where:
#   status  - one of "downloading", "finished", "error"
#   percent - download progress from 0.0 to 100.0 (or 0.0 if unknown)
#   speed   - human-readable speed string (e.g. "1.2MiB/s") or empty
#   eta     - estimated seconds remaining (or 0 if unknown)
ProgressCallback = Callable[[str, str, float, str, int], None]


def _sanitize_filename(name: str, max_length: int = 200) -> str:
    """Sanitize a string so it is safe to use as a filename.

    - Normalizes unicode to NFKD form
    - Strips characters that are unsafe on Windows/Linux/macOS
    - Collapses whitespace and trims
    - Enforces a maximum length (excluding extension)
    """
    # Normalize unicode characters
    name = unicodedata.normalize("NFKD", name)

    # Remove characters that are problematic across platforms
    # Forbidden on Windows: \ / : * ? " < > |
    # Also strip control characters (0x00-0x1f, 0x7f)
    name = re.sub(r'[\\/:*?"<>|\x00-\x1f\x7f]', "", name)

    # Replace sequences of whitespace with a single space
    name = re.sub(r"\s+", " ", name).strip()

    # Replace dots/spaces at the end (Windows dislikes trailing dots/spaces)
    name = name.rstrip(". ")

    # Truncate to max_length
    if len(name) > max_length:
        name = name[:max_length].rstrip(". ")

    # Fallback if the name ended up empty
    if not name:
        name = "untitled"

    return name


@dataclass
class DownloadResult:
    """Result of a download operation."""

    video_id: str
    title: str
    path: Path
    file_size: int  # bytes
    success: bool
    error: Optional[str] = None


class Downloader:
    """Manages downloading audio files from YouTube via yt-dlp.

    Downloads are saved as mp3 (preferred) or best available audio format
    into a configurable directory. Filenames are sanitized for cross-platform
    safety and include the video ID to guarantee uniqueness.
    """

    def __init__(
        self,
        download_dir: Optional[Path] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        config = get_config()
        self._download_dir: Path = download_dir or Path(
            config.get("download", "directory", str(Path.home() / "Music" / "wrkmon"))
        )
        self._download_dir.mkdir(parents=True, exist_ok=True)
        self._progress_callback = progress_callback

        # yt-dlp options for downloading audio
        self._ydl_opts: dict = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": "",  # set per-download
        }

    @property
    def download_dir(self) -> Path:
        """Return the current download directory."""
        return self._download_dir

    @download_dir.setter
    def download_dir(self, path: Path) -> None:
        """Set a new download directory, creating it if needed."""
        path.mkdir(parents=True, exist_ok=True)
        self._download_dir = path

    def set_progress_callback(self, callback: Optional[ProgressCallback]) -> None:
        """Set or clear the progress callback."""
        self._progress_callback = callback

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def download(self, video_id: str, title: str) -> Path:
        """Download the audio for *video_id* and return the local file path.

        If the file already exists on disk, the download is skipped and the
        existing path is returned immediately.

        Raises ``RuntimeError`` on download failure.
        """
        existing = self.get_local_path(video_id)
        if existing is not None:
            logger.info("Already downloaded: %s (%s)", title, video_id)
            return existing

        result: DownloadResult = await asyncio.to_thread(
            self._download_sync, video_id, title
        )

        if not result.success:
            raise RuntimeError(
                f"Download failed for {video_id}: {result.error or 'unknown error'}"
            )

        logger.info(
            "Downloaded %s -> %s (%d bytes)",
            video_id,
            result.path,
            result.file_size,
        )
        return result.path

    async def is_downloaded(self, video_id: str) -> bool:
        """Check whether *video_id* has already been downloaded."""
        return self.get_local_path(video_id) is not None

    def get_local_path(self, video_id: str) -> Optional[Path]:
        """Return the path to the local file for *video_id*, or ``None``.

        Scans the download directory for any file whose stem ends with the
        video ID (the naming scheme is ``<sanitized_title> [<video_id>]``).
        """
        if not self._download_dir.exists():
            return None

        # Escape brackets for glob (otherwise they're interpreted as char classes)
        pattern = f"*[[]{ video_id}[]].*"
        matches = list(self._download_dir.glob(pattern))
        if matches:
            # Prefer mp3 if multiple formats somehow exist
            for m in matches:
                if m.suffix.lower() == ".mp3":
                    return m
            return matches[0]

        return None

    # ------------------------------------------------------------------
    # Internal synchronous helpers (run inside asyncio.to_thread)
    # ------------------------------------------------------------------

    def _build_output_template(self, video_id: str, title: str) -> str:
        """Build the yt-dlp output template for a given video."""
        safe_title = _sanitize_filename(title)
        # Embed the video ID in the filename so we can reliably find it later
        stem = f"{safe_title} [{video_id}]"
        return str(self._download_dir / stem) + ".%(ext)s"

    def _make_progress_hook(self, video_id: str) -> Callable[[dict], None]:
        """Create a yt-dlp progress hook bound to *video_id*."""

        def hook(d: dict) -> None:
            if self._progress_callback is None:
                return

            status = d.get("status", "downloading")

            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes", 0)
                percent = (downloaded / total * 100.0) if total > 0 else 0.0
                speed = d.get("_speed_str", d.get("speed_str", ""))
                if not speed and d.get("speed"):
                    speed = f"{d['speed'] / 1024 / 1024:.1f}MiB/s"
                eta = int(d.get("eta", 0) or 0)
                self._progress_callback(video_id, "downloading", percent, speed, eta)

            elif status == "finished":
                self._progress_callback(video_id, "finished", 100.0, "", 0)

            elif status == "error":
                self._progress_callback(video_id, "error", 0.0, "", 0)

        return hook

    def _download_sync(self, video_id: str, title: str) -> DownloadResult:
        """Blocking download implementation (called via ``asyncio.to_thread``)."""
        url = f"https://www.youtube.com/watch?v={video_id}"
        outtmpl = self._build_output_template(video_id, title)

        opts = {
            **self._ydl_opts,
            "outtmpl": outtmpl,
            "progress_hooks": [self._make_progress_hook(video_id)],
        }

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)

                if info is None:
                    return DownloadResult(
                        video_id=video_id,
                        title=title,
                        path=Path(),
                        file_size=0,
                        success=False,
                        error="yt-dlp returned no info",
                    )

                # yt-dlp may have post-processed the file (e.g. converted to mp3).
                # The final filename is recorded in info under 'requested_downloads'.
                final_path = self._resolve_downloaded_path(info, video_id, title)

                if final_path is None or not final_path.exists():
                    return DownloadResult(
                        video_id=video_id,
                        title=title,
                        path=final_path or Path(),
                        file_size=0,
                        success=False,
                        error="Downloaded file not found on disk",
                    )

                return DownloadResult(
                    video_id=video_id,
                    title=title,
                    path=final_path,
                    file_size=final_path.stat().st_size,
                    success=True,
                )

        except Exception as e:
            logger.exception("Download failed for %s", video_id)
            # Fire the error callback so UI can react
            if self._progress_callback:
                self._progress_callback(video_id, "error", 0.0, "", 0)
            return DownloadResult(
                video_id=video_id,
                title=title,
                path=Path(),
                file_size=0,
                success=False,
                error=str(e),
            )

    def _resolve_downloaded_path(
        self, info: dict, video_id: str, title: str
    ) -> Optional[Path]:
        """Figure out the final path of the downloaded file.

        yt-dlp records the post-processed filepath in ``requested_downloads``.
        If that is missing we fall back to scanning the download directory.
        """
        # Try the info dict first (most reliable after post-processing)
        requested = info.get("requested_downloads")
        if requested:
            filepath = requested[0].get("filepath")
            if filepath:
                p = Path(filepath)
                if p.exists():
                    return p

        # Fallback: scan directory for the video ID pattern
        return self.get_local_path(video_id)
