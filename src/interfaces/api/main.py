"""
FastAPI Application Entry Point
================================
Creates and configures the FastAPI application instance.

To run in development:
    uvicorn src.interfaces.api.main:app --reload --port 8000

Rules (interfaces layer):
  - Wires everything together at startup.
  - Infrastructure initialisation (DB schema) happens in the lifespan handler.
  - No business logic here.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.sqlite_client import SQLiteClient
from src.interfaces.api.controllers.book_controller import router as books_router
from src.interfaces.api.schemas import ErrorResponse, HealthResponse

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle application startup and shutdown events."""
    logger.info(
        "Starting %s v%s in '%s' environment",
        settings.app_title,
        settings.app_version,
        settings.app_env,
    )

    # Initialise the database schema on startup
    db_client = SQLiteClient(db_path=settings.database_url)
    await db_client.initialise()
    logger.info("Database ready at '%s'", settings.database_url)

    yield  # Application is running

    logger.info("Shutting down %s", settings.app_title)


# ---------------------------------------------------------------------------
# FastAPI application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""
    _settings = get_settings()

    application = FastAPI(
        title=_settings.app_title,
        version=_settings.app_version,
        description=(
            "Mini-Library API — manage your personal book collection. "
            "Built with FastAPI and Clean Architecture."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ---- CORS ----
    application.add_middleware(
        CORSMiddleware,
        allow_origins=_settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- Routes ----
    application.include_router(books_router)

    # ---- Health check ----
    @application.get(
        "/health",
        response_model=HealthResponse,
        tags=["Health"],
        summary="Health check",
    )
    async def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            version=_settings.app_version,
            environment=_settings.app_env,
        )

    # ---- Global exception handler ----
    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: object, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="internal_server_error",
                detail="An unexpected error occurred. Please try again later.",
            ).model_dump(),
        )

    return application


# ---------------------------------------------------------------------------
# Module-level app instance (used by uvicorn)
# ---------------------------------------------------------------------------

app = create_app()
