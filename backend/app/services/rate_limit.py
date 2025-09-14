import os, time
from collections import defaultdict, deque
from fastapi import Request, HTTPException
from app.settings import settings
LLM_RATE_MAX = settings.LLM_RATE_MAX
LLM_RATE_WINDOW_SEC = settings.LLM_RATE_WINDOW_SEC

# Env-configurable; sane defaults for a laptop demo
# LLM_RATE_MAX = int(os.getenv("LLM_RATE_MAX", "30"))          # max requests
# LLM_RATE_WINDOW_SEC = int(os.getenv("LLM_RATE_WINDOW_SEC", "3600"))  # per window (seconds)

class _RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max = max_requests
        self.window = window_seconds
        self.buckets = defaultdict(deque)  # key -> deque[timestamps]

    def check(self, key: str):
        now = time.time()
        dq = self.buckets[key]
        # drop old timestamps
        while dq and (now - dq[0] > self.window):
            dq.popleft()
        if len(dq) >= self.max:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.max} requests per {self.window} seconds."
            )
        dq.append(now)

_limiter = _RateLimiter(LLM_RATE_MAX, LLM_RATE_WINDOW_SEC)

async def llm_rate_limit(request: Request):
    # simple per-IP key; works locally. (Behind proxies you’d read X-Forwarded-For.)
    ip = request.client.host if request.client else "unknown"
    _limiter.check(ip)
