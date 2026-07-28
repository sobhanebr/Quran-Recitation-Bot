"""WhatsApp Cloud API outbound client."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from src.config import get_settings

logger = logging.getLogger(__name__)


class WhatsAppClient:
    def __init__(
        self,
        token: str | None = None,
        phone_number_id: str | None = None,
        api_version: str | None = None,
        api_base: str | None = None,
    ):
        settings = get_settings()
        self.token = token if token is not None else settings.whatsapp_token
        self.phone_number_id = phone_number_id if phone_number_id is not None else settings.whatsapp_phone_number_id
        self.api_version = api_version or settings.whatsapp_api_version
        self.api_base = (api_base or settings.whatsapp_api_base).rstrip("/")

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.phone_number_id)

    def _url(self, path: str) -> str:
        return f"{self.api_base}/{self.api_version}/{self.phone_number_id}/{path.lstrip('/')}"

    async def send_text(self, to: str, body: str) -> dict[str, Any]:
        if not self.enabled:
            logger.warning("WhatsApp client disabled (missing token/phone id); skipping send to %s", to)
            return {"skipped": True, "to": to, "body": body}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": body},
        }
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self._url("messages"), json=payload, headers=headers)
            try:
                data = resp.json()
            except Exception:
                data = {"raw": resp.text}
            if resp.status_code >= 400:
                logger.error("WhatsApp send failed %s: %s", resp.status_code, data)
            return data
