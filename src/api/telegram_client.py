"""Telegram API outbound client."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from src.config import get_settings

logger = logging.getLogger(__name__)


class TelegramClient:
    def __init__(self, token: str | None = None):
        settings = get_settings()
        self.token = token if token is not None else settings.telegram_token

    @property
    def enabled(self) -> bool:
        return bool(self.token)

    async def send_text(self, chat_id: str, text: str) -> dict[str, Any]:
        if not self.enabled:
            logger.warning("Telegram client disabled (missing token); skipping send to %s", chat_id)
            return {"skipped": True, "chat_id": chat_id, "text": text}

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            try:
                data = resp.json()
            except Exception:
                data = {"raw": resp.text}
            if resp.status_code >= 400:
                logger.error("Telegram send failed %s: %s", resp.status_code, data)
            return data
