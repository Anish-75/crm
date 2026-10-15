import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.api import api_router
from app.api.v1.endpoints.health import router as health_router
from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.db.supabase import get_supabase_client
from app.logging_config import setup_logging

logger = logging.getLogger("crm.api")


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that attaches a unique X-Request-ID and logs request metrics
    (method, path, status_code, duration_ms) using structured logging.
    Ensures no PII or secrets are logged.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        # Log structured request completion (safe path without query parameters containing potential tokens)
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} ({duration_ms}ms)",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown routines."""
    settings = get_settings()
    setup_logging(log_level=settings.LOG_LEVEL)
    logger.info(
        f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]",
        extra={"environment": settings.ENVIRONMENT, "version": settings.APP_VERSION},
    )
    # Eagerly initialize Supabase client
    try:
        get_supabase_client()
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        logger.warning(f"Supabase client eager initialization warning: {e}")

    yield

    logger.info(f"Shutting down {settings.APP_NAME}")


def create_application() -> FastAPI:
    """Factory function to configure and construct the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="WooCommerce-Integrated CRM API with Supabase Auth & Role-Based Access Control",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 1. Structured Logging and Request-ID Middleware
    app.add_middleware(StructuredLoggingMiddleware)

    # 2. CORS Middleware strictly restricted to FRONTEND_ORIGIN (PRD Section 7, 10)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 3. Register custom exception handlers
    register_exception_handlers(app)

    # 4. Public Health probe at root: GET /health (PRD Section 7)
    app.include_router(health_router)

    # 5. Core API v1 routes mounted with /api/v1 prefix (PRD Section 7)
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_application()

