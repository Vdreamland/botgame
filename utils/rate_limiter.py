# -*- coding: utf-8 -*-
"""
ClawRoyale Asynchronous Token Bucket Rate Limiter.
Enforces REST and WebSocket rate limit compliance at both IP and Instance levels.
"""

import asyncio
import time

class TokenBucket:
    def __init__(self, max_tokens: float, refill_rate_per_sec: float):
        """
        Initializes a token bucket.
        :param max_tokens: Maximum capacity of the bucket.
        :param refill_rate_per_sec: Refill speed (tokens added per second).
        """
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate_per_sec
        self.tokens = max_tokens
        self.last_refill_time = time.monotonic()
        self._lock = asyncio.Lock()

    async def _refill(self) -> None:
        """Refills the token pool based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_refill_time
        if elapsed > 0:
            self.tokens = min(self.max_tokens, self.tokens + (elapsed * self.refill_rate))
            self.last_refill_time = now

    async def consume(self, tokens_needed: float = 1.0) -> None:
        """
        Consumes tokens. Suspends asynchronously if tokens are insufficient.
        """
        async with self._lock:
            while True:
                await self._refill()
                if self.tokens >= tokens_needed:
                    self.tokens -= tokens_needed
                    break
                
                missing_tokens = tokens_needed - self.tokens
                wait_time = missing_tokens / self.refill_rate
                await asyncio.sleep(wait_time)


class GlobalRateLimiter:
    """
    Central Rate Limiter Coordinator for managing REST and WebSocket limits.
    """
    def __init__(self):
        # REST: Maksimal 280 tokens, refill 4.5/detik (Target aman di bawah 300 request/menit)
        self.global_rest_limiter = TokenBucket(max_tokens=280.0, refill_rate_per_sec=4.5)

    def create_ws_limiter(self) -> TokenBucket:
        """
        Creates an isolated WS limiter for a single agent instance.
        WS: Maksimal 110 tokens, refill 1.8/detik (Target aman di bawah 120 pesan/menit)
        """
        return TokenBucket(max_tokens=110.0, refill_rate_per_sec=1.8)