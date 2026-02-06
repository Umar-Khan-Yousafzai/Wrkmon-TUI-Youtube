"""
Retry utility with exponential backoff and jitter for async functions.
"""

import asyncio
import functools
import logging
import random
from typing import Any, Callable, Tuple, Type

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
) -> Callable:
    """
    Async decorator that retries a function with exponential backoff and jitter.

    Args:
        max_retries: Maximum number of retry attempts (not counting the initial call).
        base_delay: Base delay in seconds for the first retry.
        max_delay: Maximum delay in seconds between retries.
        exceptions: Tuple of exception types to catch and retry on.

    Returns:
        A decorator that wraps an async function with retry logic.

    Raises:
        The last caught exception if all retries are exhausted.

    Example::

        @retry_with_backoff(max_retries=5, base_delay=0.5, exceptions=(ConnectionError, TimeoutError))
        async def fetch_data(url):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: BaseException | None = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc

                    if attempt == max_retries:
                        logger.error(
                            "Function '%s' failed after %d attempt(s): %s",
                            func.__qualname__,
                            max_retries + 1,
                            exc,
                        )
                        raise

                    # Exponential backoff: base_delay * 2^attempt
                    delay = base_delay * (2 ** attempt)
                    # Add jitter: randomise between 0 and the computed delay
                    jittered_delay = random.uniform(0, delay)
                    # Clamp to max_delay
                    jittered_delay = min(jittered_delay, max_delay)

                    logger.warning(
                        "Function '%s' failed on attempt %d/%d (%s: %s). "
                        "Retrying in %.2f seconds...",
                        func.__qualname__,
                        attempt + 1,
                        max_retries + 1,
                        type(exc).__name__,
                        exc,
                        jittered_delay,
                    )

                    await asyncio.sleep(jittered_delay)

            # This should be unreachable, but just in case:
            if last_exception is not None:
                raise last_exception

        return wrapper

    return decorator
