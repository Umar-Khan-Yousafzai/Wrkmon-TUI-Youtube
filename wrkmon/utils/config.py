"""Configuration management for wrkmon."""

import os
import sys
from pathlib import Path
from typing import Any

# Use tomllib for Python 3.11+, fall back to tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


class Config:
    """Manages application configuration."""

    DEFAULT_CONFIG = {
        "general": {
            "volume": 80,
            "shuffle": False,
            "repeat_mode": "none",  # none, one, all
            "show_trending_on_start": True,
        },
        "player": {
            "mpv_path": "mpv",
            "audio_only": True,
            "no_video": True,
        },
        "cache": {
            "url_ttl_hours": 6,
            "max_entries": 1000,
        },
        "ui": {
            "theme": "github_dark",  # github_dark, matrix, dracula, nord
            "show_fake_stats": True,
            "show_thumbnails": True,
            "thumbnail_style": "colored_blocks",  # colored_blocks, colored_simple, braille, blocks
            "thumbnail_width": 45,
        },
    }

    def __init__(self):
        self._config: dict[str, Any] = {}
        self._config_dir = self._get_config_dir()
        self._config_file = self._config_dir / "config.toml"
        self._data_dir = self._get_data_dir()
        self._ensure_dirs()
        self._load()

    def _get_config_dir(self) -> Path:
        """Get the configuration directory path."""
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        else:
            base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        return base / "wrkmon"

    def _get_data_dir(self) -> Path:
        """Get the data directory path."""
        if sys.platform == "win32":
            base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        else:
            base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        return base / "wrkmon"

    def _ensure_dirs(self) -> None:
        """Ensure configuration and data directories exist."""
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._data_dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> None:
        """Load configuration from file."""
        # Deep copy default config
        import copy
        self._config = copy.deepcopy(self.DEFAULT_CONFIG)

        if self._config_file.exists() and tomllib is not None:
            try:
                with open(self._config_file, "rb") as f:
                    user_config = tomllib.load(f)
                self._merge_config(user_config)
            except Exception:
                pass  # Use defaults on error

    def _merge_config(self, user_config: dict[str, Any]) -> None:
        """Merge user config into default config."""
        for section, values in user_config.items():
            if section in self._config and isinstance(values, dict):
                self._config[section].update(values)
            else:
                self._config[section] = values

    def save(self) -> None:
        """Save current configuration to file."""
        lines = []
        for section, values in self._config.items():
            lines.append(f"[{section}]")
            for key, value in values.items():
                if isinstance(value, bool):
                    lines.append(f"{key} = {str(value).lower()}")
                elif isinstance(value, str):
                    lines.append(f'{key} = "{value}"')
                else:
                    lines.append(f"{key} = {value}")
            lines.append("")

        self._config_file.write_text("\n".join(lines))

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any) -> None:
        """Set a configuration value."""
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value

    @property
    def config_dir(self) -> Path:
        """Get configuration directory path."""
        return self._config_dir

    @property
    def data_dir(self) -> Path:
        """Get data directory path."""
        return self._data_dir

    @property
    def database_path(self) -> Path:
        """Get database file path."""
        return self._data_dir / "wrkmon.db"

    @property
    def cache_path(self) -> Path:
        """Get cache file path."""
        return self._data_dir / "cache.db"

    # General settings
    @property
    def volume(self) -> int:
        """Get current volume setting."""
        return self.get("general", "volume", 80)

    @volume.setter
    def volume(self, value: int) -> None:
        """Set volume."""
        self.set("general", "volume", max(0, min(100, value)))

    @property
    def repeat_mode(self) -> str:
        """Get repeat mode (none, one, all)."""
        return self.get("general", "repeat_mode", "none")

    @repeat_mode.setter
    def repeat_mode(self, value: str) -> None:
        """Set repeat mode."""
        if value in ("none", "one", "all"):
            self.set("general", "repeat_mode", value)

    @property
    def shuffle(self) -> bool:
        """Get shuffle setting."""
        return self.get("general", "shuffle", False)

    @shuffle.setter
    def shuffle(self, value: bool) -> None:
        """Set shuffle."""
        self.set("general", "shuffle", value)

    @property
    def show_trending_on_start(self) -> bool:
        """Whether to show trending videos on startup."""
        return self.get("general", "show_trending_on_start", True)

    @show_trending_on_start.setter
    def show_trending_on_start(self, value: bool) -> None:
        """Set show trending on start."""
        self.set("general", "show_trending_on_start", value)

    # Player settings
    @property
    def mpv_path(self) -> str:
        """Get mpv executable path."""
        from wrkmon.utils.mpv_installer import get_mpv_path
        configured = self.get("player", "mpv_path", "mpv")
        if configured != "mpv":
            return configured
        return get_mpv_path()

    # Cache settings
    @property
    def url_ttl_hours(self) -> int:
        """Get URL cache TTL in hours."""
        return self.get("cache", "url_ttl_hours", 6)

    # UI settings
    @property
    def theme(self) -> str:
        """Get UI theme."""
        return self.get("ui", "theme", "github_dark")

    @theme.setter
    def theme(self, value: str) -> None:
        """Set UI theme."""
        self.set("ui", "theme", value)

    @property
    def show_thumbnails(self) -> bool:
        """Whether to show thumbnails."""
        return self.get("ui", "show_thumbnails", True)

    @show_thumbnails.setter
    def show_thumbnails(self, value: bool) -> None:
        """Set show thumbnails."""
        self.set("ui", "show_thumbnails", value)

    @property
    def thumbnail_style(self) -> str:
        """Get thumbnail rendering style."""
        return self.get("ui", "thumbnail_style", "colored_blocks")

    @thumbnail_style.setter
    def thumbnail_style(self, value: str) -> None:
        """Set thumbnail style."""
        if value in ("colored_blocks", "colored_simple", "braille", "blocks"):
            self.set("ui", "thumbnail_style", value)

    @property
    def thumbnail_width(self) -> int:
        """Get thumbnail width in characters."""
        return self.get("ui", "thumbnail_width", 45)

    @thumbnail_width.setter
    def thumbnail_width(self, value: int) -> None:
        """Set thumbnail width."""
        self.set("ui", "thumbnail_width", max(20, min(80, value)))


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
