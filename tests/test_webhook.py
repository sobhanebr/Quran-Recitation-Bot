from fastapi.testclient import TestClient


def test_health_and_webhook_verify(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 't.db'}")
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "test-verify")
    # Reset cached settings + engine for this process
    from src.config import get_settings
    from src import models as models_pkg
    from src.models import db as db_mod

    get_settings.cache_clear()
    db_mod.engine = db_mod._make_engine()
    db_mod.SessionLocal = db_mod.sessionmaker(bind=db_mod.engine, autoflush=False, autocommit=False)

    from src.main import app

    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    bad = client.get(
        "/webhook",
        params={"hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "123"},
    )
    assert bad.status_code == 403

    ok = client.get(
        "/webhook",
        params={"hub.mode": "subscribe", "hub.verify_token": "test-verify", "hub.challenge": "12345"},
    )
    assert ok.status_code == 200
    assert ok.text == "12345"


def test_webhook_message_flow(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 't2.db'}")
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "test-verify")
    monkeypatch.setenv("WHATSAPP_TOKEN", "")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "")

    from src.config import get_settings
    from src.models import db as db_mod

    get_settings.cache_clear()
    db_mod.engine = db_mod._make_engine()
    db_mod.SessionLocal = db_mod.sessionmaker(bind=db_mod.engine, autoflush=False, autocommit=False)

    from src.main import app

    client = TestClient(app)
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": "pn"},
                            "contacts": [{"wa_id": "15551234567", "profile": {"name": "Ali"}}],
                            "messages": [
                                {
                                    "from": "15551234567",
                                    "id": "wamid.1",
                                    "type": "text",
                                    "text": {"body": "/help"},
                                }
                            ],
                        }
                    }
                ]
            }
        ],
    }
    resp = client.post("/webhook", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
