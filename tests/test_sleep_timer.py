"""Tests for the SleepTimer module."""

import asyncio
import pytest
from wrkmon.core.sleep_timer import SleepTimer


@pytest.fixture
def timer():
    return SleepTimer()


class TestSleepTimer:
    """Tests for SleepTimer."""

    def test_initial_state(self, timer):
        assert not timer.is_active
        assert timer.remaining_seconds == 0.0
        assert timer.remaining_minutes == 0.0

    @pytest.mark.asyncio
    async def test_start_sets_active(self, timer):
        await timer.start(1.0)
        assert timer.is_active
        assert timer.remaining_seconds > 0
        await timer.stop()

    @pytest.mark.asyncio
    async def test_start_invalid_duration(self, timer):
        with pytest.raises(ValueError, match="positive"):
            await timer.start(0)
        with pytest.raises(ValueError, match="positive"):
            await timer.start(-5)

    @pytest.mark.asyncio
    async def test_stop_cancels_timer(self, timer):
        await timer.start(10.0)
        assert timer.is_active
        await timer.stop()
        assert not timer.is_active
        assert timer.remaining_seconds == 0.0

    @pytest.mark.asyncio
    async def test_reset_restarts(self, timer):
        await timer.start(5.0)
        await timer.reset(10.0)
        assert timer.is_active
        # Duration should be ~10 minutes now
        assert timer.remaining_seconds > 5 * 60
        await timer.stop()

    @pytest.mark.asyncio
    async def test_reset_same_duration(self, timer):
        await timer.start(5.0)
        await asyncio.sleep(0.05)
        await timer.reset()
        assert timer.is_active
        # Should have restarted with 5 minutes
        assert timer.remaining_seconds > 4.9 * 60
        await timer.stop()

    @pytest.mark.asyncio
    async def test_callback_fires(self, timer):
        fired = []

        async def on_expire():
            fired.append(True)

        timer.set_callback(on_expire)
        await timer.start(0.001)  # Very short timer (~0.06 seconds)
        await asyncio.sleep(0.2)
        assert len(fired) == 1

    @pytest.mark.asyncio
    async def test_callback_not_called_on_stop(self, timer):
        fired = []

        async def on_expire():
            fired.append(True)

        timer.set_callback(on_expire)
        await timer.start(10.0)
        await timer.stop()
        await asyncio.sleep(0.1)
        assert len(fired) == 0

    @pytest.mark.asyncio
    async def test_remaining_decreases(self, timer):
        await timer.start(1.0)
        r1 = timer.remaining_seconds
        await asyncio.sleep(0.1)
        r2 = timer.remaining_seconds
        assert r2 < r1
        await timer.stop()

    @pytest.mark.asyncio
    async def test_remaining_minutes(self, timer):
        await timer.start(2.0)
        assert timer.remaining_minutes <= 2.0
        assert timer.remaining_minutes > 1.9
        await timer.stop()

    @pytest.mark.asyncio
    async def test_double_start_restarts(self, timer):
        await timer.start(5.0)
        await timer.start(10.0)
        # Should be ~10 minutes, not 5
        assert timer.remaining_seconds > 9 * 60
        await timer.stop()
