__all__ = ["limiter"]

from aiolimiter import AsyncLimiter
import asyncio

# 90 calls per minute.
rate_limiter = AsyncLimiter(max_rate=3, time_period=2)


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
limiter = lambda f: (lambda *a, **kw: rate_limited_call(f, *a, **kw))
