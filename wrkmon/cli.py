"""CLI entry point for wrkmon using Typer."""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from wrkmon import __version__

app = typer.Typer(
    name="wrkmon",
    help="Work Monitor - A developer productivity tool",
    no_args_is_help=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"wrkmon version {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """
    Work Monitor - Monitor and manage system processes.

    Run without arguments to launch the interactive monitor.
    """
    if ctx.invoked_subcommand is None:
        # Launch TUI
        from wrkmon.app import run_app
        run_app()


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum results"),
) -> None:
    """Search for processes to monitor."""
    from wrkmon.core.youtube import YouTubeClient
    from wrkmon.utils.stealth import get_stealth

    stealth = get_stealth()

    async def do_search():
        client = YouTubeClient()
        results = await client.search(query, max_results=limit)
        return results

    console.print(f"[dim]Searching for: {query}[/dim]\n")

    results = asyncio.run(do_search())

    if not results:
        console.print("[yellow]No results found[/yellow]")
        return

    table = Table(title="Search Results")
    table.add_column("#", style="dim")
    table.add_column("Process Name")
    table.add_column("PID", style="dim")
    table.add_column("Duration")
    table.add_column("Status", style="green")

    for i, result in enumerate(results, 1):
        process_name = stealth.get_fake_process_name(result.title)
        fake_pid = str(stealth.get_fake_pid())
        duration = result.duration_str
        table.add_row(str(i), process_name[:50], fake_pid, duration, "READY")

    console.print(table)
    console.print(f"\n[dim]Use 'wrkmon play <id>' to start a process[/dim]")


@app.command()
def play(
    video_id: str = typer.Argument(..., help="Video ID or URL to play"),
) -> None:
    """Play a specific process by ID or URL."""
    import re

    # Extract video ID from URL if needed
    if "youtube.com" in video_id or "youtu.be" in video_id:
        # Extract ID from URL
        patterns = [
            r"(?:v=|/)([a-zA-Z0-9_-]{11})",
            r"youtu\.be/([a-zA-Z0-9_-]{11})",
        ]
        for pattern in patterns:
            match = re.search(pattern, video_id)
            if match:
                video_id = match.group(1)
                break

    from wrkmon.core.youtube import YouTubeClient
    from wrkmon.core.player import AudioPlayer
    from wrkmon.core.cache import Cache
    from wrkmon.utils.stealth import get_stealth

    stealth = get_stealth()
    cache = Cache()

    async def do_play():
        client = YouTubeClient()
        player = AudioPlayer()

        # Get stream info
        console.print("[dim]Getting process info...[/dim]")

        # Check cache
        cached = cache.get(video_id)
        if cached:
            audio_url = cached.audio_url
            title = cached.title
        else:
            stream_info = await client.get_stream_url(video_id)
            if not stream_info:
                console.print("[red]Failed to get process info[/red]")
                return False

            audio_url = stream_info.audio_url
            title = stream_info.title

            # Cache it
            cache.set(
                video_id=video_id,
                title=stream_info.title,
                channel=stream_info.channel,
                duration=stream_info.duration,
                audio_url=audio_url,
            )

        # Start player
        console.print("[dim]Starting process...[/dim]")
        if not await player.start():
            console.print("[red]Failed to start player[/red]")
            return False

        # Play
        if await player.play(audio_url):
            process_name = stealth.get_fake_process_name(title)
            console.print(f"[green]Running:[/green] {process_name}")
            console.print("[dim]Press Ctrl+C to stop[/dim]")

            # Keep running until interrupted
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopping process...[/yellow]")
            finally:
                await player.shutdown()

            return True
        else:
            console.print("[red]Failed to start process[/red]")
            return False

    asyncio.run(do_play())


@app.command()
def queue() -> None:
    """Show the current process queue."""
    # For CLI, we show an empty queue message since queue is session-based
    console.print("[dim]No processes in queue[/dim]")
    console.print("[dim]Run 'wrkmon' to use the interactive monitor[/dim]")


@app.command()
def history(
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum entries to show"),
) -> None:
    """Show process history."""
    from wrkmon.data.database import Database
    from wrkmon.utils.stealth import get_stealth

    stealth = get_stealth()
    db = Database()

    entries = db.get_history(limit=limit)

    if not entries:
        console.print("[dim]No history yet[/dim]")
        return

    table = Table(title="Process History")
    table.add_column("#", style="dim")
    table.add_column("Process Name")
    table.add_column("Duration")
    table.add_column("Runs", style="cyan")
    table.add_column("Last Run", style="dim")

    for i, entry in enumerate(entries, 1):
        process_name = stealth.get_fake_process_name(entry.track.title)
        duration = entry.track.duration_str
        runs = str(entry.play_count)
        last_run = entry.played_at.strftime("%Y-%m-%d %H:%M")
        table.add_row(str(i), process_name[:40], duration, runs, last_run)

    console.print(table)
    db.close()


@app.command()
def playlists() -> None:
    """List all playlists."""
    from wrkmon.data.database import Database

    db = Database()
    playlists = db.get_all_playlists()

    if not playlists:
        console.print("[dim]No playlists yet[/dim]")
        console.print("[dim]Run 'wrkmon' to create playlists[/dim]")
        return

    table = Table(title="Playlists")
    table.add_column("#", style="dim")
    table.add_column("Name")
    table.add_column("Tracks", style="cyan")
    table.add_column("Created", style="dim")

    for i, playlist in enumerate(playlists, 1):
        created = playlist.created_at.strftime("%Y-%m-%d") if playlist.created_at else "N/A"
        table.add_row(str(i), playlist.name, str(playlist.track_count), created)

    console.print(table)
    db.close()


@app.command()
def clear_cache() -> None:
    """Clear the URL cache."""
    from wrkmon.core.cache import Cache

    cache = Cache()
    stats = cache.get_stats()
    count = cache.clear()

    console.print(f"[green]Cleared {count} cached entries[/green]")


@app.command()
def clear_history() -> None:
    """Clear play history."""
    from wrkmon.data.database import Database

    db = Database()
    count = db.clear_history()
    db.close()

    console.print(f"[green]Cleared {count} history entries[/green]")


@app.command()
def config() -> None:
    """Show configuration info."""
    from wrkmon.utils.config import get_config

    cfg = get_config()

    console.print("[bold]Configuration[/bold]\n")
    console.print(f"Config directory: {cfg.config_dir}")
    console.print(f"Data directory: {cfg.data_dir}")
    console.print(f"Database: {cfg.database_path}")
    console.print(f"Cache: {cfg.cache_path}")
    console.print(f"\nVolume: {cfg.volume}%")
    console.print(f"Cache TTL: {cfg.url_ttl_hours} hours")


@app.command()
def update(
    check_only: bool = typer.Option(
        False, "--check", "-c", help="Only check for updates, don't install"
    ),
) -> None:
    """Check for and install updates."""
    from wrkmon.utils.updater import check_for_updates, perform_update

    console.print("[dim]Checking for updates...[/dim]")

    update_info = check_for_updates()

    if update_info is None:
        console.print("[yellow]Could not check for updates. Please try again later.[/yellow]")
        return

    console.print(f"Current version: [cyan]{update_info.current_version}[/cyan]")
    console.print(f"Latest version:  [cyan]{update_info.latest_version}[/cyan]")

    if not update_info.is_update_available:
        console.print("\n[green]You are running the latest version![/green]")
        return

    console.print(f"\n[yellow]Update available![/yellow]")

    if check_only:
        console.print(f"\nTo update, run: [bold]{update_info.update_command}[/bold]")
        return

    # Prompt for update
    if typer.confirm("Do you want to update now?"):
        console.print("[dim]Updating...[/dim]")
        success, message = perform_update()
        if success:
            console.print(f"[green]{message}[/green]")
        else:
            console.print(f"[red]{message}[/red]")
    else:
        console.print(f"\nTo update later, run: [bold]{update_info.update_command}[/bold]")


@app.command()
def deps() -> None:
    """Check and manage dependencies."""
    from wrkmon.utils.updater import check_dependencies, get_deno_install_command
    from wrkmon.utils.mpv_installer import is_mpv_installed, get_mpv_path

    console.print("[bold]Dependency Status[/bold]\n")

    deps_status = check_dependencies()

    table = Table()
    table.add_column("Dependency", style="bold")
    table.add_column("Status")
    table.add_column("Required")
    table.add_column("Description", style="dim")

    for name, info in deps_status.items():
        if name == "js_runtime":
            continue  # Skip aggregate

        status = "[green]Installed[/green]" if info["installed"] else "[red]Missing[/red]"
        required = "[yellow]Yes[/yellow]" if info["required"] else "No"
        table.add_row(name, status, required, info["description"])

    console.print(table)

    # Show recommendations
    if not deps_status["mpv"]["installed"]:
        console.print("\n[red]mpv is required for audio playback![/red]")
        console.print("Install with:")
        console.print("  [bold]Linux:[/bold]   sudo apt install mpv")
        console.print("  [bold]macOS:[/bold]   brew install mpv")
        console.print("  [bold]Windows:[/bold] winget install mpv")

    if not deps_status["js_runtime"]["installed"]:
        console.print("\n[yellow]No JavaScript runtime found.[/yellow]")
        console.print("For better YouTube compatibility, install deno:")
        console.print(f"  [bold]{get_deno_install_command()}[/bold]")


@app.command()
def install_deno() -> None:
    """Install deno for better YouTube compatibility."""
    from wrkmon.utils.updater import install_deno as do_install_deno, is_deno_installed

    if is_deno_installed():
        console.print("[green]deno is already installed![/green]")
        return

    console.print("[dim]Attempting to install deno...[/dim]")
    success, message = do_install_deno()

    if success:
        console.print(f"[green]{message}[/green]")
    else:
        console.print(f"[yellow]{message}[/yellow]")


if __name__ == "__main__":
    app()
