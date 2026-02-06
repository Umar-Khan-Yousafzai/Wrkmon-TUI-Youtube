"""Sleep timer for automatic playback stop after a set duration."""

import asyncio
import logging
import time
from typing import Awaitable, Callable, Optional, Union

logger = logging.getLogger("wrkmon.sleep_timer")

Callback = Union[Callable[[], None], Callable[[], Awaitable[None]]]


class SleepTimer:
    """Countdown timer that fires a callback when it expires."""

    def __init__(self, callback: Optional[Callback] = None) -> None:
        self._callback = callback
        self._duration_seconds: float = 0.0
        self._task: Optional[asyncio.Task] = None
        self._active: bool = False
        self._started_at: Optional[float] = None

    @property
    def is_active(self) -> bool:
        return self._active and self._task is not None and not self._task.done()

    @property
    def remaining_seconds(self) -> float:
        if not self.is_active or self._started_at is None:
            return 0.0
        elapsed = time.monotonic() - self._started_at
        return max(0.0, self._duration_seconds - elapsed)

    @property
    def remaining_minutes(self) -> float:
        return self.remaining_seconds / 60.0

    def set_callback(self, callback: Callback) -> None:
        self._callback = callback

    async def start(self, minutes: float) -> None:
        """Start (or restart) the timer for the given minutes."""
        if minutes <= 0:
            raise ValueError("Timer duration must be positive.")
        await self.stop()
        self._duration_seconds = minutes * 60.0
        self._started_at = time.monotonic()
        self._active = True
        self._task = asyncio.create_task(self._countdown())
        logger.info("Sleep timer started for %.1f minute(s).", minutes)

    async def stop(self) -> None:
        """Cancel the timer without firing the callback."""
        if self._task is not None and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._cleanup()

    async def reset(self, minutes: Optional[float] = None) -> None:
        """Reset the timer with optional new duration."""
        duration = minutes if minutes is not None else (self._duration_seconds / 60.0)
        if duration <= 0:
            return
        await self.start(duration)

    async def _countdown(self) -> None:
        try:
            await asyncio.sleep(self._duration_seconds)
            logger.info("Sleep timer expired.")
            self._active = False
            await self._fire_callback()
        except asyncio.CancelledError:
            raise
        finally:
            self._cleanup()

    async def _fire_callback(self) -> None:
        if self._callback is None:
            return
        try:
            result = self._callback()
            if asyncio.iscoroutine(result):
                await result
        except Exception:
            logger.exception("Error in sleep timer callback.")

    def _cleanup(self) -> None:
        self._active = False
        self._started_at = None
        self._task = None
