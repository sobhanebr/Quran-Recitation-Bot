"""SQLAlchemy engine and session helpers."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config import get_settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    settings = get_settings()
    
    # Fix for Vercel Postgres (SQLAlchemy 1.4+ requires postgresql://)
    url = settings.database_url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
        
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    from src import models  # noqa: F401 — register models

    if settings_needs_sqlite_dir():
        ensure_sqlite_parent()
    Base.metadata.create_all(bind=engine)
    _apply_column_migrations()


def _apply_column_migrations() -> None:
    """Idempotently add columns introduced after a table already existed.

    The legacy ``weeks`` / ``juz_claims`` tables were replaced by ``cycles`` /
    ``portion_claims``; old dev databases should simply be reset (see README).
    """
    from sqlalchemy import inspect, text

    new_group_columns = {
        "granularity": "VARCHAR(16) NOT NULL DEFAULT 'juz'",
        "cycle_spec": "VARCHAR(16) NOT NULL DEFAULT 'weekly'",
        "reminder_spec": "VARCHAR(16) NOT NULL DEFAULT 'daily'",
        "ad_spec": "VARCHAR(16) NOT NULL DEFAULT 'off'",
        "last_reminder_at": "DATETIME",
        "last_ad_at": "DATETIME",
    }
    inspector = inspect(engine)
    if "groups" not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns("groups")}
    with engine.begin() as conn:
        for name, ddl in new_group_columns.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE groups ADD COLUMN {name} {ddl}"))


def settings_needs_sqlite_dir() -> bool:
    return get_settings().database_url.startswith("sqlite:///")


def ensure_sqlite_parent() -> None:
    from pathlib import Path

    url = get_settings().database_url
    path = Path(url.removeprefix("sqlite:///"))
    path.parent.mkdir(parents=True, exist_ok=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
