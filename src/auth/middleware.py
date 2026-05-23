import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.auth.config import auth_settings
from src.auth.rate_limiter import RateLimiter

rate_limiter = RateLimiter()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        identifier = f"ip:{client_ip}"

        if not rate_limiter.is_allowed(identifier):
            return Response(
                content='{"detail":"Rate limit excedido. Tente novamente mais tarde."}',
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": str(auth_settings.rate_limit_window_seconds),
                    "X-RateLimit-Limit": str(auth_settings.rate_limit_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        remaining = rate_limiter.remaining(identifier)
        response.headers["X-RateLimit-Limit"] = str(auth_settings.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        start = time.time()

        request.state.request_id = request_id

        response = await call_next(request)

        duration_ms = round((time.time() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms}ms"

        return response


def register_middlewares(app: FastAPI) -> None:
    app.add_middleware(AuditLogMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
