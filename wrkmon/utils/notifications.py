"""
Cross-platform system notifications module with async support.

Supports Linux (notify-send), macOS (osascript), and Windows (plyer / PowerShell).
All public functions are async and will fail silently if the notification cannot be
delivered.
"""

import asyncio
import logging
import sys

logger = logging.getLogger(__name__)


async def send_notification(title: str, body: str, timeout: int = 5) -> None:
    """
    Send a desktop notification on the current platform.

    The call is fully async -- it will never block the event loop.  If the
    notification cannot be delivered for any reason the function returns
    silently (the error is logged at debug level).

    Args:
        title: Notification title / summary.
        body: Notification body text.
        timeout: Display duration in seconds (best-effort, not all platforms
                 honour this).
    """
    try:
        if sys.platform.startswith("linux"):
            await _send_linux(title, body, timeout)
        elif sys.platform == "darwin":
            await _send_macos(title, body, timeout)
        elif sys.platform == "win32":
            await _send_windows(title, body, timeout)
        else:
            logger.debug(
                "Notifications not supported on platform '%s'", sys.platform
            )
    except Exception:
        logger.debug(
            "Failed to send notification (title=%r)", title, exc_info=True
        )


# ---------------------------------------------------------------------------
# Platform-specific helpers
# ---------------------------------------------------------------------------


async def _send_linux(title: str, body: str, timeout: int) -> None:
    """Send a notification on Linux via ``notify-send``."""
    timeout_ms = str(timeout * 1000)
    proc = await asyncio.create_subprocess_exec(
        "notify-send",
        "--expire-time",
        timeout_ms,
        "--",
        title,
        body,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()


async def _send_macos(title: str, body: str, timeout: int) -> None:
    """Send a notification on macOS via ``osascript``."""
    # AppleScript escaping: replace backslashes then double-quotes.
    escaped_title = title.replace("\\", "\\\\").replace('"', '\\"')
    escaped_body = body.replace("\\", "\\\\").replace('"', '\\"')

    script = (
        f'display notification "{escaped_body}" '
        f'with title "{escaped_title}"'
    )

    proc = await asyncio.create_subprocess_exec(
        "osascript",
        "-e",
        script,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()


async def _send_windows(title: str, body: str, timeout: int) -> None:
    """Send a notification on Windows via *plyer* or PowerShell toast."""
    # Try plyer first -- it produces nicer native toasts.
    if await _send_windows_plyer(title, body, timeout):
        return

    # Fallback: PowerShell BalloonTip.
    await _send_windows_powershell(title, body, timeout)


async def _send_windows_plyer(title: str, body: str, timeout: int) -> bool:
    """Attempt to send a notification using the *plyer* library.

    Returns ``True`` on success, ``False`` if plyer is unavailable.
    """
    try:
        from plyer import notification as plyer_notification  # type: ignore[import-untyped]
    except ImportError:
        return False

    def _notify() -> None:
        plyer_notification.notify(
            title=title,
            message=body,
            timeout=timeout,
        )

    await asyncio.to_thread(_notify)
    return True


async def _send_windows_powershell(title: str, body: str, timeout: int) -> None:
    """Fallback: show a Windows toast notification via PowerShell."""
    # Escape single quotes for PowerShell strings.
    ps_title = title.replace("'", "''")
    ps_body = body.replace("'", "''")

    # Use the Windows built-in BalloonTip via PowerShell.
    ps_script = (
        "[void][System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms');"
        "$n = New-Object System.Windows.Forms.NotifyIcon;"
        "$n.Icon = [System.Drawing.SystemIcons]::Information;"
        "$n.Visible = $true;"
        f"$n.ShowBalloonTip({timeout * 1000}, '{ps_title}', '{ps_body}', "
        "'Info');"
        f"Start-Sleep -Seconds {timeout};"
        "$n.Dispose();"
    )

    proc = await asyncio.create_subprocess_exec(
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        ps_script,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()
