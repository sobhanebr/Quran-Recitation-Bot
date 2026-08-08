"""Tests for /cron/tick auth and WhatsApp template proactive sends."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def cron_client(monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "test-cron-secret")
    monkeypatch.setenv("ENABLE_INLINE_SCHEDULER", "false")
    monkeypatch.setenv("WHATSAPP_TEMPLATE_REMINDER", "quran_reminder")
    # Settings are lru_cached — clear before importing app
    from src.config import get_settings

    get_settings.cache_clear()
    from src.main import app

    with TestClient(app) as client:
        yield client
    get_settings.cache_clear()


def test_cron_tick_unauthorized(cron_client):
    resp = cron_client.get("/cron/tick")
    assert resp.status_code == 401


def test_cron_tick_with_header(cron_client):
    with patch("src.api.cron.run_tick", new_callable=AsyncMock) as tick:
        tick.return_value = {"ok": True, "sent": 2, "queued": 2}
        resp = cron_client.get("/cron/tick", headers={"X-Cron-Secret": "test-cron-secret"})
    assert resp.status_code == 200
    assert resp.json()["sent"] == 2
    tick.assert_awaited_once()


def test_cron_tick_with_query_secret(cron_client):
    with patch("src.api.cron.run_tick", new_callable=AsyncMock) as tick:
        tick.return_value = {"ok": True, "sent": 0, "queued": 0}
        resp = cron_client.post("/cron/tick?secret=test-cron-secret")
    assert resp.status_code == 200
    tick.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_proactive_prefers_template(monkeypatch):
    monkeypatch.setenv("WHATSAPP_TOKEN", "tok")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "123")
    monkeypatch.setenv("WHATSAPP_TEMPLATE_REMINDER", "quran_reminder")
    from src.config import get_settings

    get_settings.cache_clear()
    from src.api.whatsapp_client import WhatsAppClient

    client = WhatsAppClient()
    with patch.object(client, "send_template", new_callable=AsyncMock) as tmpl:
        tmpl.return_value = {"messages": [{"id": "wamid.1"}]}
        with patch.object(client, "send_text", new_callable=AsyncMock) as text:
            result = await client.send_proactive(
                "15551234567",
                "full body",
                kind="reminder",
                lang="en",
                template_params=["Juz 1"],
            )
    assert result["messages"]
    tmpl.assert_awaited_once()
    text.assert_not_awaited()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_send_proactive_text_when_no_template(monkeypatch):
    monkeypatch.setenv("WHATSAPP_TOKEN", "tok")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "123")
    monkeypatch.setenv("WHATSAPP_TEMPLATE_REMINDER", "")
    from src.config import get_settings

    get_settings.cache_clear()
    from src.api.whatsapp_client import WhatsAppClient

    client = WhatsAppClient()
    with patch.object(client, "send_template", new_callable=AsyncMock) as tmpl:
        with patch.object(client, "send_text", new_callable=AsyncMock) as text:
            text.return_value = {"messages": [{"id": "wamid.2"}]}
            result = await client.send_proactive(
                "15551234567",
                "full body",
                kind="reminder",
                lang="en",
                template_params=["Juz 1"],
            )
    assert result["messages"]
    text.assert_awaited_once()
    tmpl.assert_not_awaited()
    get_settings.cache_clear()
