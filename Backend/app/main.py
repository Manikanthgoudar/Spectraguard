import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.logging_config import logger
# Import models so SQLAlchemy metadata is populated (needed for create_all)
from app.models import User, ReferenceSpectrum, Test, SpectraData, Report  # noqa: F401
from app.routers import auth, spectra, classify, tests, reference, reports, admin


# ── App Lifespan ────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create directories. Shutdown: cleanup (if needed)."""
    for d in [settings.UPLOAD_DIR, settings.REPORTS_DIR, settings.SAMPLE_DATA_DIR]:
        os.makedirs(d, exist_ok=True)
    logger.info("SpectraGuard API starting up...")
    yield
    logger.info("SpectraGuard API shutting down.")


# ── FastAPI App ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="SpectraGuard API",
    description=(
        "AI-based pharmaceutical authentication system using Raman spectroscopy. "
        "Upload spectral CSV data and get instant drug authenticity classification."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Exception Handler ────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please try again.",
            "detail": str(exc) if settings.APP_ENV == "development" else None,
        },
    )


# ── Routers ─────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(spectra.router)
app.include_router(classify.router)
app.include_router(tests.router)
app.include_router(reference.router)
app.include_router(reports.router)
app.include_router(admin.router)


# ── Health Check ────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "SpectraGuard API",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
    }


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to SpectraGuard API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }
