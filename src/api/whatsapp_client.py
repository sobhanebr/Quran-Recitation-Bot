"""WhatsApp Cloud API outbound client (session text + template messages)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from src.config import get_settings

logger = logging.getLogger(__name__)

# Free-form text outside the 24h customer-service window
WINDOW_CLOSED_CODES = {131047, 470}


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

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _error_code(data: dict[str, Any]) -> int | None:
        err = data.get("error") if isinstance(data, dict) else None
        if not isinstance(err, dict):
            return None
        code = err.get("code")
        return int(code) if code is not None else None

    @staticmethod
    def _ok(data: dict[str, Any]) -> bool:
        return bool(data.get("messages") or data.get("skipped")) and "error" not in data

    async def _post_messages(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self._url("messages"), json=payload, headers=self._headers())
            try:
                data = resp.json()
            except Exception:
                data = {"raw": resp.text}
            if resp.status_code >= 400:
                logger.error("WhatsApp send failed %s: %s", resp.status_code, data)
            return data if isinstance(data, dict) else {"raw": data}

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
        return await self._post_messages(payload)

    async def send_template(
        self,
        to: str,
        name: str,
        language: str,
        body_params: list[str] | None = None,
    ) -> dict[str, Any]:
        """Send an approved message template (works outside the 24h window)."""
        if not self.enabled:
            logger.warning("WhatsApp client disabled; skipping template to %s", to)
            return {"skipped": True, "to": to, "template": name}

        template: dict[str, Any] = {
            "name": name,
            "language": {"code": language},
        }
        if body_params:
            template["components"] = [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": str(p)} for p in body_params],
                }
            ]

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": template,
        }
        return await self._post_messages(payload)

    async def send_proactive(
        self,
        to: str,
        body: str,
        *,
        kind: str,
        lang: str = "en",
        template_params: list[str] | None = None,
    ) -> dict[str, Any]:
        """Send a scheduled/proactive message.

        Prefers an approved template when configured for ``kind`` (required outside
        the 24h window). Falls back to free-form text; if text hits error 131047 and
        a template exists, retries as a template.
        """
        settings = get_settings()
        template_name = settings.whatsapp_template_name(kind)
        template_lang = settings.whatsapp_template_lang(lang)
        params = template_params or []

        if template_name:
            result = await self.send_template(to, template_name, template_lang, params)
            if self._ok(result):
                return result
            logger.warning(
                "Template %s failed for %s (%s); falling back to free-form text",
                template_name,
                to,
                result.get("error"),
            )

        result = await self.send_text(to, body)
        if self._ok(result):
            return result

        code = self._error_code(result)
        if code in WINDOW_CLOSED_CODES and not template_name:
            logger.error(
                "Cannot message %s outside 24h window and no template configured for kind=%s",
                to,
                kind,
            )
        elif code in WINDOW_CLOSED_CODES and template_name:
            logger.error(
                "Free-form blocked for %s (code %s) and template %s already failed",
                to,
                code,
                template_name,
            )
        return result
