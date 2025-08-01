"""Module rate limiter call support"""

__all__ = ["limiter"]

import asyncio
from aiolimiter import AsyncLimiter

# 180 calls per minute.
rate_limiter = AsyncLimiter(max_rate=6, time_period=2)


async def rate_limited_call(func, *args, **kwargs):
    """Calls a function with rate limiting.

    Example usage:
      ...
      existing_content = await limiter(wiki.page_text)(title)
    """
    async with rate_limiter:
        return await asyncio.to_thread(func, *args, **kwargs)


# Example usage:
#   existing_content = await limiter(wiki.page_text)(title)
def limiter(f):
    """Create a rate-limited version of the given function."""

    def rate_limited_function(*args, **kwargs):
        return rate_limited_call(f, *args, **kwargs)

    return rate_limited_function
