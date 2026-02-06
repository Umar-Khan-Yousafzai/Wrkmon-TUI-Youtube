"""Tests for the retry utility."""

import pytest
from wrkmon.utils.retry import retry_with_backoff


class TestRetryWithBackoff:
    """Tests for retry_with_backoff decorator."""

    @pytest.mark.asyncio
    async def test_succeeds_first_try(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        async def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await succeed()
        assert result == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_failure(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        async def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("fail")
            return "ok"

        result = await fail_twice()
        assert result == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self):
        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.01)
        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("always fails")

        with pytest.raises(ValueError, match="always fails"):
            await always_fail()

        assert call_count == 3  # 1 initial + 2 retries

    @pytest.mark.asyncio
    async def test_only_catches_specified_exceptions(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01, exceptions=(ConnectionError,))
        async def fail_with_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("not retried")

        with pytest.raises(TypeError):
            await fail_with_type_error()

        assert call_count == 1  # No retries for TypeError

    @pytest.mark.asyncio
    async def test_preserves_function_name(self):
        @retry_with_backoff()
        async def my_special_function():
            return 42

        assert my_special_function.__name__ == "my_special_function"
