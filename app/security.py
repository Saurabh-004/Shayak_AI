import time
from collections import defaultdict, deque
from fastapi import HTTPException, Request
from app.config import get_settings


class RateLimiter:
    def __init__(self) -> None:
        self.events: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, limit: int) -> None:
        now = time.monotonic()
        bucket = self.events[key]
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= limit:
            raise HTTPException(429, detail="Please wait a minute before checking more messages.")
        bucket.append(now)


limiter = RateLimiter()


def client_key(request: Request, kind: str) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{host}:{kind}"


def apply_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self'; script-src 'self'; "
        "img-src 'self' data:; connect-src 'self'; base-uri 'self'; frame-ancestors 'none'"
    )
    return response


async def limit_analysis(request: Request, kind: str = "analysis") -> None:
    settings = get_settings()
    limit = 3 if kind == "image" else settings.rate_limit_per_minute
    limiter.check(client_key(request, kind), limit)
