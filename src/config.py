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
    # In-process APScheduler (set false on Vercel; use /cron/tick via cron-job.org instead)
    enable_inline_scheduler: bool = True

    # Shared secret for GET/POST /cron/tick (header X-Cron-Secret, Bearer, or ?secret=)
    cron_secret: str = ""

    # Approved WhatsApp template names (empty = free-form text only; fails outside 24h window)
    whatsapp_template_reminder: str = ""
    whatsapp_template_ad: str = ""
    whatsapp_template_cycle: str = ""
    whatsapp_template_plan: str = ""
    # Default Meta template language code when group lang has no mapping
    whatsapp_template_lang_default: str = "en"

    # Vercel Postgres automatically injects this
    postgres_url: str | None = None

    @property
    def bootstrap_admins(self) -> set[str]:
        return {x.strip() for x in self.bootstrap_admin_ids.split(",") if x.strip()}

    def whatsapp_template_name(self, kind: str) -> str:
        return {
            "reminder": self.whatsapp_template_reminder,
            "ad": self.whatsapp_template_ad,
            "cycle_rollover": self.whatsapp_template_cycle,
            "plan_checkin": self.whatsapp_template_plan,
        }.get(kind, "")

    def whatsapp_template_lang(self, lang: str | None) -> str:
        """Map bot language codes to Meta template language codes."""
        mapping = {
            "en": "en",
            "fa": "fa",
            "ar": "ar",
        }
        code = (lang or "").strip().lower()
        return mapping.get(code, self.whatsapp_template_lang_default)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.postgres_url:
        settings.database_url = settings.postgres_url
    return settings
