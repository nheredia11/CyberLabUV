"""CyberLabUV API — punto de entrada.

La lógica de cada dominio vive en app/routers/*.py. Aquí solo se construye la
aplicación: ciclo de vida, CORS, cabeceras de seguridad y registro de routers.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .cleanup import cleanup_expired_sessions, start_cleanup_scheduler
from .config import get_settings
from .database import init_db
from .routers import (
    auth, checkpoints, consent, health, modules,
    scenarios, students, surveys, teacher,
)

logger = logging.getLogger("cyberlab")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await cleanup_expired_sessions()
    cleanup_task = asyncio.create_task(start_cleanup_scheduler(interval_seconds=300))
    yield
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


is_prod = getattr(settings, "app_env", "development").lower() == "production"

app = FastAPI(
    title="CyberLabUV API",
    lifespan=lifespan,
    docs_url=None if is_prod else "/docs",
    redoc_url=None if is_prod else "/redoc",
    openapi_url=None if is_prod else "/openapi.json",
)

cors_origins = getattr(settings, "cors_origins", ["http://localhost:5173", "http://127.0.0.1:5173"])
if isinstance(cors_origins, str):
    cors_origins = [o.strip() for o in cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# El orden importa solo dentro de un mismo router (p. ej. /command antes de /{action}).
for _module in (health, auth, modules, surveys, checkpoints, teacher, students, scenarios, consent):
    app.include_router(_module.router)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    if request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception("Error interno no controlado: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "detail": "Error interno del servidor. Por favor, intente más tarde."},
    )
