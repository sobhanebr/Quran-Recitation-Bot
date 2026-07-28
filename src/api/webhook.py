"""WhatsApp Cloud API webhook routes."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from src.api.whatsapp_client import WhatsAppClient
from src.bot.handlers import handle_message
from src.config import get_settings
from src.models.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["whatsapp"])


def _extract_messages(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize Cloud API webhook payload into message dicts."""
    out: list[dict[str, Any]] = []
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            value = change.get("value") or {}
            contacts = {c.get("wa_id"): c for c in (value.get("contacts") or [])}
            metadata = value.get("metadata") or {}
            for msg in value.get("messages") or []:
                if msg.get("type") != "text":
                    continue
                wa_id = msg.get("from")
                contact = contacts.get(wa_id) or {}
                profile = contact.get("profile") or {}
                out.append(
                    {
                        "from": wa_id,
                        "text": ((msg.get("text") or {}).get("body") or "").strip(),
                        "name": profile.get("name") or wa_id or "",
                        # Cloud API group support varies; use chat id when present
                        "chat_id": msg.get("group_id") or wa_id,
                        "phone_number_id": metadata.get("phone_number_id"),
                        "message_id": msg.get("id"),
                    }
                )
    return out


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
):
    settings = get_settings()
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return Response(content=hub_challenge or "", media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    messages = _extract_messages(payload)
    client = WhatsAppClient()
    for msg in messages:
        try:
            reply = handle_message(
                db,
                chat_id=msg["chat_id"],
                user_id=msg["from"],
                display_name=msg["name"],
                text=msg["text"],
            )
            if reply:
                await client.send_text(msg["from"], reply)
        except Exception:
            logger.exception("Failed handling message from %s", msg.get("from"))
    return {"status": "ok"}
