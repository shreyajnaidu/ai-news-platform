"""
app/main.py
===========
Entry point for the FastAPI application.

This file does THREE things:
  1. Creates the FastAPI app instance
  2. Registers a startup/shutdown lifecycle
  3. Includes all route handlers

ROUTES REGISTERED:
------------------
  /auth/*        → signup, login, profile, interests
  /articles/*    → AI summarization
  /*             → news feed routes (prefix defined in news router)
  /health        → simple liveness check
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.news import router as news_router
from app.api.summarize import router as summarize_router
from app.api.auth import router as auth_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup / shutdown lifecycle.
    """

    # ── Startup ─────────────────────────────────────────────
    print(f"✓ API started: {settings.app_name}")

    yield

    # ── Shutdown ────────────────────────────────────────────
    print("✓ API shutdown complete")


# ── FastAPI App ────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)


# ── CORS ───────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://ai-news-frontend-vwzz.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ─────────────────────────────────────────────────

# News feed routes
app.include_router(news_router)

# AI summarization routes
app.include_router(
    summarize_router,
    prefix="/articles",
    tags=["summarize"],
)

# Authentication routes — signup, login, profile, interests
app.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"],
)


# ── Health Check ───────────────────────────────────────────

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
    }
