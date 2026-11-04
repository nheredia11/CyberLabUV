"""Rate limiting en memoria (por IP y por usuario)."""
from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, Request

request_counts: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(key_prefix: str, max_requests: int, window_seconds: int = 60):
    def limiter(request: Request):
        client_ip = request.client.host if request.client else "unknown"
        key = f"{key_prefix}:{client_ip}"
        now = time.time()
        request_counts[key] = [t for t in request_counts[key] if now - t < window_seconds]
        if len(request_counts[key]) >= max_requests:
            raise HTTPException(status_code=429, detail="Demasiadas solicitudes. Por favor intente más tarde.")
        request_counts[key].append(now)
    return limiter

def check_user_rate_limit(key_prefix: str, max_requests: int, window_seconds: int = 60):
    def limiter(user_id: str):
        key = f"{key_prefix}:{user_id}"
        now = time.time()
        request_counts[key] = [t for t in request_counts[key] if now - t < window_seconds]
        if len(request_counts[key]) >= max_requests:
            raise HTTPException(status_code=429, detail="Demasiadas solicitudes. Por favor intente más tarde.")
        request_counts[key].append(now)
    return limiter
