"""Quran Juz Sharing WhatsApp bot — FastAPI entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from src.api.telegram_webhook import router as telegram_webhook_router
from src.api.webhook import router as webhook_router
from src.config import get_settings
from src.models.db import init_db
from src.services.scheduler_service import run_tick

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

settings = get_settings()


# Initialize database tables on startup (Vercel bypasses ASGI lifespan sometimes)
init_db()

@asynccontextmanager
async def lifespan(_app: FastAPI):
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        run_tick,
        "interval",
        seconds=settings.scheduler_interval_seconds,
        id="quran-bot-tick",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.include_router(webhook_router)
app.include_router(telegram_webhook_router)


from fastapi.responses import RedirectResponse

@app.get("/")
def read_root():
    return RedirectResponse(url="https://t.me/holy_quran_recitation_bot")

@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}
