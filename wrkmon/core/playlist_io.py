"""Playlist import/export functionality for wrkmon."""

import json
import logging
from pathlib import Path
from typing import Optional

from wrkmon.data.models import Playlist, Track

logger = logging.getLogger("wrkmon.playlist_io")


def export_playlist(playlist: Playlist, filepath: Path, format: str = "json") -> bool:
    """Export a playlist to a file.

    Args:
        playlist: The playlist to export
        filepath: Destination file path
        format: 'json' or 'm3u'

    Returns:
        True if successful
    """
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            return _export_json(playlist, filepath)
        elif format == "m3u":
            return _export_m3u(playlist, filepath)
        else:
            logger.error(f"Unknown export format: {format}")
            return False
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return False


def import_playlist(filepath: Path) -> Optional[dict]:
    """Import a playlist from a file.

    Returns:
        Dict with 'name', 'description', 'tracks' list of dicts,
        or None on failure.
    """
    try:
        suffix = filepath.suffix.lower()
        if suffix == ".json":
            return _import_json(filepath)
        elif suffix in (".m3u", ".m3u8"):
            return _import_m3u(filepath)
        else:
            logger.error(f"Unknown import format: {suffix}")
            return None
    except Exception as e:
        logger.error(f"Import failed: {e}")
        return None


def _export_json(playlist: Playlist, filepath: Path) -> bool:
    """Export playlist as JSON."""
    data = {
        "name": playlist.name,
        "description": playlist.description,
        "track_count": playlist.track_count,
        "total_duration": playlist.total_duration,
        "tracks": [
            {
                "video_id": t.video_id,
                "title": t.title,
                "channel": t.channel,
                "duration": t.duration,
                "url": t.url,
            }
            for t in playlist.tracks
        ],
    }
    filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    logger.info(f"Exported {playlist.track_count} tracks to {filepath}")
    return True


def _export_m3u(playlist: Playlist, filepath: Path) -> bool:
    """Export playlist as M3U."""
    lines = ["#EXTM3U", f"#PLAYLIST:{playlist.name}"]
    for track in playlist.tracks:
        lines.append(f"#EXTINF:{track.duration},{track.title} - {track.channel}")
        lines.append(track.url)
    filepath.write_text("\n".join(lines) + "\n")
    logger.info(f"Exported {playlist.track_count} tracks to {filepath}")
    return True


def _import_json(filepath: Path) -> Optional[dict]:
    """Import playlist from JSON."""
    data = json.loads(filepath.read_text())
    if "tracks" not in data:
        logger.error("Invalid JSON playlist: missing 'tracks' key")
        return None
    return {
        "name": data.get("name", filepath.stem),
        "description": data.get("description", ""),
        "tracks": data["tracks"],
    }


def _import_m3u(filepath: Path) -> Optional[dict]:
    """Import playlist from M3U."""
    import re

    lines = filepath.read_text().strip().split("\n")
    name = filepath.stem
    tracks = []
    current_info = {}

    for line in lines:
        line = line.strip()
        if line.startswith("#PLAYLIST:"):
            name = line[10:].strip()
        elif line.startswith("#EXTINF:"):
            # Parse: #EXTINF:duration,title - artist
            match = re.match(r"#EXTINF:(\d+),(.+)", line)
            if match:
                current_info = {
                    "duration": int(match.group(1)),
                    "title": match.group(2).strip(),
                }
        elif line and not line.startswith("#"):
            # This is a URL line
            video_id = _extract_video_id(line)
            if video_id:
                track = {
                    "video_id": video_id,
                    "title": current_info.get("title", "Unknown"),
                    "channel": "Unknown",
                    "duration": current_info.get("duration", 0),
                }
                tracks.append(track)
            current_info = {}

    return {"name": name, "description": f"Imported from {filepath.name}", "tracks": tracks}


def _extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from a YouTube URL."""
    import re

    patterns = [
        r"(?:v=|/)([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None
