import uuid
import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("observability")

class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()

        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        correlation_id = request.headers.get("X-Correlation-ID") or request_id

        # Attach to request state for downstream handlers
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id

        response: Response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Inject tracing headers into response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Response-Time-Ms"] = str(duration_ms)

        # Log structured request summary
        logger.info(
            f"HTTP {request.method} {request.url.path} finished with status {response.status_code} in {duration_ms}ms",
            extra={
                "request_id": request_id,
                "correlation_id": correlation_id,
                "http_method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": duration_ms
            }
        )

        return response
