"""Application settings for the Quran WhatsApp bot."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Quran Juz Sharing Bot"
    database_url: str = f"sqlite:///{Path(__file__).resolve().parent.parent / 'data' / 'quran_bot.db'}"

    # Meta WhatsApp Cloud API
    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = "quran-bot-verify"
    whatsapp_api_version: str = "v21.0"
    whatsapp_api_base: str = "https://graph.facebook.com"

    # Telegram API
    telegram_token: str = ""
    telegram_secret_token: str = ""

    # Comma-separated WhatsApp user IDs that are global super-admins
    bootstrap_admin_ids: str = ""

    default_language: str = "en"

    # Seconds between scheduler ticks (cycle rollover, reminders, ads, plan check-ins)
    scheduler_interval_seconds: int = 300

    @property
    def bootstrap_admins(self) -> set[str]:
        return {x.strip() for x in self.bootstrap_admin_ids.split(",") if x.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
