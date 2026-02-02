"""Main TUI application for wrkmon - properly structured with Textual best practices."""

import asyncio
import logging
import sys
from pathlib import Path

# Setup logging to file
log_path = Path.home() / ".wrkmon_debug.log"
logging.basicConfig(
    filename=str(log_path),
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("wrkmon.app")
logger.info(f"=== WRKMON STARTED === Log file: {log_path}")

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Footer, ContentSwitcher

from wrkmon.core.youtube import YouTubeClient, SearchResult
from wrkmon.core.player import AudioPlayer
from wrkmon.core.queue import PlayQueue
from wrkmon.core.cache import Cache
from wrkmon.data.database import Database
from wrkmon.utils.config import get_config
from wrkmon.utils.stealth import get_stealth

from wrkmon.ui.theme import APP_CSS
from wrkmon.ui.widgets.header import HeaderBar
from wrkmon.ui.widgets.player_bar import PlayerBar
from wrkmon.ui.views.search import SearchView
from wrkmon.ui.views.queue import QueueView
from wrkmon.ui.views.history import HistoryView
from wrkmon.ui.views.playlists import PlaylistsView
from wrkmon.ui.messages import (
    TrackSelected,
    TrackQueued,
    StatusMessage,
    PlaybackStateChanged,
)
from wrkmon.utils.updater import (
    check_for_updates_async,
    check_dependencies,
    get_js_runtime,
    install_deno_async,
)


class WrkmonApp(App):
    """Main wrkmon TUI application with proper Textual architecture."""

    CSS = APP_CSS
    TITLE = "wrkmon"

    BINDINGS = [
        # Global navigation (priority so they work even when input focused)
        Binding("f1", "switch_view('search')", "Search", show=True, priority=True),
        Binding("f2", "switch_view('queue')", "Queue", show=True, priority=True),
        Binding("f3", "switch_view('history')", "History", show=True, priority=True),
        Binding("f4", "switch_view('playlists')", "Lists", show=True, priority=True),
        # Playback controls (global)
        Binding("f5", "toggle_pause", "Play/Pause", show=True, priority=True),
        Binding("f6", "volume_down", "Vol-", show=True, priority=True),
        Binding("f7", "volume_up", "Vol+", show=True, priority=True),
        Binding("f8", "next_track", "Next", show=True, priority=True),
        Binding("f9", "stop", "Stop", show=True, priority=True),
        Binding("f10", "queue_current", "Queue", show=True, priority=True),
        # Additional controls (when not in input)
        Binding("space", "toggle_pause", "Play/Pause", show=False),
        Binding("+", "volume_up", "Vol+", show=False),
        Binding("=", "volume_up", "Vol+", show=False),
        Binding("-", "volume_down", "Vol-", show=False),
        Binding("n", "next_track", "Next", show=False),
        Binding("p", "prev_track", "Prev", show=False),
        Binding("s", "stop", "Stop", show=False),
        # App controls
        Binding("escape", "focus_search", "Back", show=False, priority=True),
        Binding("ctrl+c", "quit", "Quit", show=False, priority=True),
        Binding("ctrl+q", "quit", "Quit", show=False, priority=True),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Load config
        self._config = get_config()
        self._stealth = get_stealth()

        # Core services
        self.youtube = YouTubeClient()
        self.player = AudioPlayer()
        self.queue = PlayQueue()
        self.cache = Cache()
        self.database = Database()

        # State
        self._volume = self._config.volume
        self._current_track: SearchResult | None = None
        self._current_view = "search"

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        # Header (docked top)
        yield HeaderBar()

        # Main content area with view switcher
        with Container(id="content-area"):
            with ContentSwitcher(initial="search"):
                yield SearchView(id="search")
                yield QueueView(id="queue")
                yield HistoryView(id="history")
                yield PlaylistsView(id="playlists")

        # Player bar (docked bottom)
        yield PlayerBar()

        # Footer with key hints
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize app on mount."""
        # Set terminal title
        self._stealth.set_terminal_title("wrkmon")

        # Check for updates in background
        self._check_for_updates_task = asyncio.create_task(self._check_for_updates())

        # Check dependencies
        await self._check_dependencies()

        # Check if mpv is available
        from wrkmon.utils.mpv_installer import is_mpv_installed, ensure_mpv_installed

        if not is_mpv_installed():
            success, msg = ensure_mpv_installed()
            if not success:
                # Show error in player bar
                player_bar = self._get_player_bar()
                player_bar.update_playback(
                    title="mpv not found! Run: winget install mpv",
                    is_playing=False
                )
                self.notify(
                    "mpv is required for audio playback.\n"
                    "Install with: winget install mpv",
                    title="mpv Not Found",
                    severity="error",
                    timeout=10
                )
            else:
                # Try to start player
                await self.player.start()
        else:
            # Start the audio player
            started = await self.player.start()
            if not started:
                self._get_player_bar().update_playback(
                    title="Failed to start mpv",
                    is_playing=False
                )

        # Set initial volume
        if self.player.is_connected:
            await self.player.set_volume(self._volume)
        self._get_player_bar().set_volume(self._volume)

        # Start periodic updates
        self.set_interval(1.0, self._update_playback_display)

        # Update header view indicator
        self._get_header().set_view_name("search")

    async def _check_for_updates(self) -> None:
        """Check for updates in background."""
        try:
            update_info = await check_for_updates_async()
            if update_info and update_info.is_update_available:
                self._get_header().set_update_info(
                    available=True,
                    version=update_info.latest_version
                )
                self.notify(
                    f"New version {update_info.latest_version} available!\n"
                    f"Run: {update_info.update_command}",
                    title="Update Available",
                    timeout=8
                )
                logger.info(f"Update available: {update_info.latest_version}")
        except Exception as e:
            logger.debug(f"Update check failed: {e}")

    async def _check_dependencies(self) -> None:
        """Check optional dependencies and notify user."""
        try:
            js_runtime = get_js_runtime()
            if not js_runtime:
                # No JavaScript runtime - suggest installing deno
                self.notify(
                    "Install deno for better YouTube compatibility:\n"
                    "curl -fsSL https://deno.land/install.sh | sh",
                    title="Tip: Install deno",
                    timeout=6
                )
                logger.info("No JavaScript runtime found, suggesting deno installation")
        except Exception as e:
            logger.debug(f"Dependency check failed: {e}")

    # ----------------------------------------
    # Component getters
    # ----------------------------------------
    def _get_header(self) -> HeaderBar:
        """Get the header bar widget."""
        return self.query_one(HeaderBar)

    def _get_player_bar(self) -> PlayerBar:
        """Get the player bar widget."""
        return self.query_one(PlayerBar)

    def _get_content_switcher(self) -> ContentSwitcher:
        """Get the content switcher."""
        return self.query_one(ContentSwitcher)

    # ----------------------------------------
    # Message handlers
    # ----------------------------------------
    async def on_track_selected(self, message: TrackSelected) -> None:
        """Handle track selection for playback."""
        await self.play_track(message.result)

    def on_track_queued(self, message: TrackQueued) -> None:
        """Handle adding track to queue."""
        logger.info(f"=== TrackQueued received: {message.result.title} ===")
        pos = self.add_to_queue(message.result)
        logger.info(f"  Added at position: {pos}")
        logger.info(f"  Queue length now: {self.queue.length}")
        logger.info(f"  Queue current_index: {self.queue.current_index}")

    def on_status_message(self, message: StatusMessage) -> None:
        """Handle status messages (could show in a notification area)."""
        # For now, just log or ignore
        pass

    # ----------------------------------------
    # Playback methods
    # ----------------------------------------
    async def play_track(self, result: SearchResult) -> bool:
        """Play a track from search result."""
        logger.info(f"=== play_track called: {result.title} ===")
        logger.info(f"  video_id: {result.video_id}")

        self._current_track = result
        player_bar = self._get_player_bar()
        player_bar.update_playback(title=f"Loading: {result.title[:30]}...", is_playing=False)

        # Check cache first
        cached = self.cache.get(result.video_id)
        if cached:
            audio_url = cached.audio_url
            logger.info(f"  Cache HIT, audio_url: {audio_url[:80]}...")
        else:
            logger.info("  Cache MISS, fetching stream URL...")
            # Get stream URL
            player_bar.update_playback(title=f"Fetching: {result.title[:30]}...")
            stream_info = await self.youtube.get_stream_url(result.video_id)
            if not stream_info:
                logger.error("  FAILED to get stream URL!")
                player_bar.update_playback(title="ERROR: Failed to get stream URL", is_playing=False)
                return False

            audio_url = stream_info.audio_url
            logger.info(f"  Got audio_url: {audio_url[:80]}...")

            # Cache it
            self.cache.set(
                video_id=result.video_id,
                title=result.title,
                channel=result.channel,
                duration=result.duration,
                audio_url=audio_url,
            )

        # Check if player is connected
        logger.info(f"  player.is_connected: {self.player.is_connected}")
        if not self.player.is_connected:
            logger.info("  Starting player...")
            player_bar.update_playback(title="Starting player...")
            started = await self.player.start()
            logger.info(f"  player.start() returned: {started}")
            if not started:
                logger.error("  FAILED to start player!")
                player_bar.update_playback(
                    title="ERROR: mpv not found! Install mpv first.",
                    is_playing=False
                )
                return False

        # Play
        logger.info("  Calling player.play()...")
        player_bar.update_playback(title=f"Buffering: {result.title[:30]}...")
        success = await self.player.play(audio_url)
        logger.info(f"  player.play() returned: {success}")

        if success:
            logger.info("  SUCCESS - audio should be playing!")
            player_bar.update_playback(title=result.title, is_playing=True)

            # Add to history
            track = self.database.get_or_create_track(
                video_id=result.video_id,
                title=result.title,
                channel=result.channel,
                duration=result.duration,
            )
            self.database.add_to_history(track)

            # Add to queue if empty
            if self.queue.is_empty:
                self.add_to_queue(result)
                self.queue.jump_to(0)
        else:
            logger.error("  FAILED - player.play() returned False!")
            player_bar.update_playback(
                title="ERROR: Playback failed - check mpv installation",
                is_playing=False
            )

        return success

    def add_to_queue(self, result: SearchResult) -> int:
        """Add a track to the queue."""
        return self.queue.add_search_result(result)

    async def toggle_pause(self) -> None:
        """Toggle play/pause."""
        await self.player.toggle_pause()
        is_playing = self.player.is_playing
        self._get_player_bar().is_playing = is_playing

    async def set_volume(self, volume: int) -> None:
        """Set volume level."""
        self._volume = max(0, min(100, volume))
        await self.player.set_volume(self._volume)
        self._get_player_bar().set_volume(self._volume)

    async def play_next(self) -> None:
        """Play next track in queue."""
        next_item = self.queue.next()
        if next_item:
            result = SearchResult(
                video_id=next_item.video_id,
                title=next_item.title,
                channel=next_item.channel,
                duration=next_item.duration,
                view_count=0,
            )
            await self.play_track(result)

    async def play_previous(self) -> None:
        """Play previous track in queue."""
        prev_item = self.queue.previous()
        if prev_item:
            result = SearchResult(
                video_id=prev_item.video_id,
                title=prev_item.title,
                channel=prev_item.channel,
                duration=prev_item.duration,
                view_count=0,
            )
            await self.play_track(result)

    # ----------------------------------------
    # Periodic updates
    # ----------------------------------------
    async def _update_playback_display(self) -> None:
        """Update the player bar with current playback position."""
        player_bar = self._get_player_bar()

        # Always sync repeat mode to player bar
        try:
            player_bar.repeat_mode = self.queue.repeat_mode
        except Exception:
            pass

        if not self._current_track:
            return

        try:
            # Get current position and duration via IPC
            pos = await self.player.get_position()
            dur = await self.player.get_duration()
            if dur == 0:
                dur = self._current_track.duration
            is_playing = self.player.is_playing

            player_bar.update_playback(
                position=pos,
                duration=dur,
                is_playing=is_playing,
            )

            # Update queue view if visible
            if self._current_view == "queue":
                queue_view = self.query_one("#queue", QueueView)
                queue_view.update_now_playing(
                    self._current_track.title, pos, dur
                )

            # Check if track ended
            if dur > 0 and pos >= dur - 1:
                await self._on_track_end()

        except Exception:
            pass

    async def _on_track_end(self) -> None:
        """Handle track end - play next."""
        next_item = self.queue.next()
        if next_item:
            result = SearchResult(
                video_id=next_item.video_id,
                title=next_item.title,
                channel=next_item.channel,
                duration=next_item.duration,
                view_count=0,
            )
            await self.play_track(result)

    # ----------------------------------------
    # Actions
    # ----------------------------------------
    def action_switch_view(self, view_name: str) -> None:
        """Switch to a different view."""
        switcher = self._get_content_switcher()
        switcher.current = view_name
        self._current_view = view_name
        self._get_header().set_view_name(view_name)

        # Refresh queue view when switching to it
        if view_name == "queue":
            try:
                self.query_one("#queue", QueueView).refresh_queue()
            except Exception:
                pass
        # Auto-focus list when switching to search (if has results)
        elif view_name == "search":
            try:
                self.query_one("#search", SearchView).focus_list()
            except Exception:
                pass

    async def action_toggle_pause(self) -> None:
        """Smart play/pause - starts playback if nothing playing."""
        logger.info("=== F5 PRESSED: action_toggle_pause ===")
        logger.info(f"  player.is_connected: {self.player.is_connected}")
        logger.info(f"  _current_track: {self._current_track}")
        logger.info(f"  queue.is_empty: {self.queue.is_empty}")
        logger.info(f"  queue.length: {self.queue.length}")
        logger.info(f"  queue.current: {self.queue.current}")

        # If player is actively playing, just toggle pause
        if self.player.is_connected and self._current_track:
            logger.info("  -> Toggling pause (already playing)")
            await self.toggle_pause()
            return

        # Nothing playing - if in search view with selected item, play it
        if self._current_view == "search":
            try:
                search_view = self.query_one("#search", SearchView)
                result = search_view._get_selected()
                if result:
                    logger.info(f"  -> Playing selected search result: {result.title}")
                    await self.play_track(result)
                    return
            except Exception:
                pass

        # Nothing playing - try to play from queue
        current = self.queue.current
        if current:
            logger.info(f"  -> Playing current queue item: {current.title}")
            # Play the current queue item
            result = SearchResult(
                video_id=current.video_id,
                title=current.title,
                channel=current.channel,
                duration=current.duration,
                view_count=0,
            )
            await self.play_track(result)
        elif not self.queue.is_empty:
            logger.info("  -> Queue has items, jumping to first")
            # Queue has items but no current - start from first
            self.queue.jump_to(0)
            first = self.queue.current
            if first:
                logger.info(f"  -> Playing first item: {first.title}")
                result = SearchResult(
                    video_id=first.video_id,
                    title=first.title,
                    channel=first.channel,
                    duration=first.duration,
                    view_count=0,
                )
                await self.play_track(result)
        else:
            logger.warning("  -> Queue is EMPTY, cannot play")
            # Queue is empty - notify user
            self._get_player_bar().update_playback(
                title="Queue empty - search and add tracks first",
                is_playing=False
            )

    async def action_volume_up(self) -> None:
        """Increase volume."""
        await self.set_volume(self._volume + 5)

    async def action_volume_down(self) -> None:
        """Decrease volume."""
        await self.set_volume(self._volume - 5)

    async def action_next_track(self) -> None:
        """Play next track."""
        await self.play_next()

    async def action_prev_track(self) -> None:
        """Play previous track."""
        await self.play_previous()

    async def action_stop(self) -> None:
        """Stop playback completely."""
        logger.info("=== F9 PRESSED: action_stop ===")
        await self.player.stop()
        self._current_track = None
        self._get_player_bar().update_playback(
            title="Stopped",
            is_playing=False,
            position=0,
            duration=0,
        )
        logger.info("  Playback stopped")

    def action_queue_current(self) -> None:
        """Queue the currently highlighted search result (F10)."""
        logger.info("=== F10 PRESSED: action_queue_current ===")
        if self._current_view != "search":
            logger.info("  Not in search view, ignoring")
            return

        try:
            search_view = self.query_one("#search", SearchView)
            result = search_view._get_selected()
            if result:
                logger.info(f"  Queueing: {result.title}")
                pos = self.add_to_queue(result)
                self.notify(f"Queued: {result.title[:30]}...", timeout=2)
                logger.info(f"  Added at position: {pos}, queue length: {self.queue.length}")
            else:
                logger.warning("  No item selected")
                self.notify("Select a track first", severity="warning", timeout=2)
        except Exception as e:
            logger.exception(f"  Error: {e}")

    def action_focus_search(self) -> None:
        """Switch to search view and focus input."""
        self.action_switch_view("search")
        try:
            self.query_one("#search", SearchView).focus_input()
        except Exception:
            pass

    async def action_quit(self) -> None:
        """Quit the application cleanly."""
        await self._cleanup()
        self.exit()

    async def _cleanup(self) -> None:
        """Clean up resources."""
        logger.info("=== Cleaning up ===")
        # Save config
        self._config.volume = self._volume
        self._config.save()

        # Shutdown player - MUST stop mpv
        logger.info("  Stopping player...")
        await self.player.shutdown()

        # Close database
        self.database.close()

        # Restore terminal
        self._stealth.restore_terminal_title()
        logger.info("  Cleanup done")

    async def on_unmount(self) -> None:
        """Called when app is unmounting - ensure cleanup."""
        await self._cleanup()


def run_app() -> None:
    """Run the wrkmon application."""
    import atexit
    import signal

    app = WrkmonApp()

    def cleanup_on_exit():
        """Ensure mpv is killed on exit."""
        if app.player._process:
            try:
                app.player._process.terminate()
                app.player._process.wait(timeout=1)
            except Exception:
                try:
                    app.player._process.kill()
                except Exception:
                    pass

    atexit.register(cleanup_on_exit)

    # Handle Ctrl+C gracefully
    def handle_sigint(signum, frame):
        cleanup_on_exit()
        raise SystemExit(0)

    if sys.platform != "win32":
        signal.signal(signal.SIGINT, handle_sigint)

    try:
        app.run()
    finally:
        cleanup_on_exit()


if __name__ == "__main__":
    run_app()
