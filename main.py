"""
TrendWriter — LinkedIn Content Automation & Growth Intelligence System
FastAPI entry point
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from agents import (
    AsyncOpenAI,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)

from db.database import init_db
from routers import content, schedule, publish, analytics, strategy, users

load_dotenv()

# ── SDK / Gemini config (mirrors your scraper pattern) ────────────────────────
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set.")

# Tell the openai-agents SDK to not look for OPENAI_API_KEY
os.environ.setdefault("OPENAI_API_KEY", api_key)
client = AsyncOpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=api_key,
)
set_default_openai_api("chat_completions")
set_default_openai_client(client=client)
set_tracing_disabled(True)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("✅  TrendWriter API started — DB ready")
    yield
    print("🛑  TrendWriter API shutting down")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="TrendWriter",
    description="LinkedIn Content Automation & Growth Intelligence System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(users.router,     prefix="/users",     tags=["Users"])
app.include_router(content.router,   prefix="/content",   tags=["Content Generation"])
app.include_router(schedule.router,  prefix="/schedule",  tags=["Scheduling"])
app.include_router(publish.router,   prefix="/publish",   tags=["Publishing"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(strategy.router,  prefix="/strategy",  tags=["Strategy"])


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "TrendWriter",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
