"""Shared pytest fixtures with isolated SQLite DB."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure settings load before app imports mutate engine
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("WHATSAPP_VERIFY_TOKEN", "test-verify")
os.environ.setdefault("DEFAULT_LANGUAGE", "en")
os.environ.setdefault("BOOTSTRAP_ADMIN_IDS", "")
os.environ.setdefault("ENABLE_INLINE_SCHEDULER", "false")
os.environ.setdefault("CRON_SECRET", "")


@pytest.fixture()
def db_session():
    from src.models.db import Base
    from src.models import entities  # noqa: F401

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
