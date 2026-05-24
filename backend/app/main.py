from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.news import router as news_router
from app.api.summarize import router as summarize_router
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


# ── Health Check ───────────────────────────────────────────

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
    }