"""Telegram Serverless webhook route."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from src.bot.handlers import handle_message
from src.config import get_settings
from src.models.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["telegram"])


@router.post("/telegram/webhook")
async def receive_telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    # Validate secret token if configured
    if settings.telegram_secret_token:
        if x_telegram_bot_api_secret_token != settings.telegram_secret_token:
            raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if "callback_query" in payload:
        cb = payload["callback_query"]
        message = cb.get("message", {})
        text = cb.get("data", "").strip()
        sender = cb.get("from", {})
        chat = message.get("chat", {})
    else:
        message = payload.get("message")
        if not message:
            return {"status": "ok"}
        text = message.get("text", "").strip()
        sender = message.get("from", {})
        chat = message.get("chat", {})

    if not text:
        return {"status": "ok"}

    chat_id = chat.get("id")
    user_id = sender.get("id")
    if not chat_id or not user_id:
        return {"status": "ok"}

    first_name = sender.get("first_name") or ""
    last_name = sender.get("last_name") or ""
    display_name = f"{first_name} {last_name}".strip() or str(user_id)

    chat_title = chat.get("title")

    if text == "/start":
        reply_text = "Welcome! Please select a language.\nخوش آمدید! لطفا زبان را انتخاب کنید.\nأهلاً بك! الرجاء اختيار اللغة."
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": reply_text,
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {"text": "English 🇬🇧", "callback_data": "/lang en"},
                        {"text": "فارسی 🇮🇷", "callback_data": "/lang fa"},
                        {"text": "العربية 🇸🇦", "callback_data": "/lang ar"}
                    ]
                ]
            }
        }

    if text.startswith("/tg_settings"):
        parts = text.split()
        if len(parts) == 2:
            menu = parts[1]
            if menu == "unit":
                reply_text = "Select Recitation Unit:"
                reply_markup = {"inline_keyboard": [
                    [{"text": "Page", "callback_data": "/granularity page"}, {"text": "Surah", "callback_data": "/granularity surah"}],
                    [{"text": "Hizb", "callback_data": "/granularity hizb"}, {"text": "Juz", "callback_data": "/granularity juz"}, {"text": "Quran", "callback_data": "/granularity quran"}]
                ]}
            elif menu == "cycle":
                reply_text = "Select Cycle Length:"
                reply_markup = {"inline_keyboard": [
                    [{"text": "Daily", "callback_data": "/cycle daily"}, {"text": "Weekly", "callback_data": "/cycle weekly"}],
                    [{"text": "Monthly", "callback_data": "/cycle monthly"}]
                ]}
            elif menu == "rem":
                reply_text = "Select Reminder Frequency:"
                reply_markup = {"inline_keyboard": [
                    [{"text": "Off", "callback_data": "/reminders off"}, {"text": "Daily", "callback_data": "/reminders daily"}],
                    [{"text": "Every 12h", "callback_data": "/reminders 12h"}, {"text": "Every 2d", "callback_data": "/reminders 2d"}]
                ]}
            elif menu == "ads":
                reply_text = "Select Open-Spot Ads Frequency:"
                reply_markup = {"inline_keyboard": [
                    [{"text": "Off", "callback_data": "/advertise off"}, {"text": "Daily", "callback_data": "/advertise daily"}],
                    [{"text": "Every 12h", "callback_data": "/advertise 12h"}, {"text": "Every 2d", "callback_data": "/advertise 2d"}]
                ]}
            else:
                return {"status": "ok"}
                
            return {
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": reply_text,
                "reply_markup": reply_markup
            }

    try:
        from src.bot.commands import parse_command
        parsed = parse_command(text)

        reply = handle_message(
            db,
            chat_id=f"tg:{chat_id}",
            user_id=f"tg:{user_id}",
            display_name=display_name,
            text=text,
            chat_title=chat_title,
        )
        if reply:
            from src.services.group_service import QuranGroupService
            svc = QuranGroupService(db)
            group = svc.get_or_create_group(f"tg:{chat_id}")
            lang = group.language

            if lang == "fa":
                kb = [
                    [{"text": "وضعیت"}, {"text": "آزاد"}],
                    [{"text": "رزرو"}, {"text": "تمام"}, {"text": "من"}],
                    [{"text": "راهنما"}, {"text": "تنظیمات"}]
                ]
            elif lang == "ar":
                kb = [
                    [{"text": "حالة"}, {"text": "متاح"}],
                    [{"text": "حجز"}, {"text": "تم"}, {"text": "لي"}],
                    [{"text": "مساعدة"}, {"text": "اعدادات"}]
                ]
            else:
                kb = [
                    [{"text": "Status"}, {"text": "Available"}],
                    [{"text": "Claim"}, {"text": "Done"}, {"text": "Mine"}],
                    [{"text": "Help"}, {"text": "Settings"}]
                ]

            inline_kb = None
            if parsed and parsed.action == "claim" and not parsed.args:
                available = svc.available_portions(group)
                if available.ok:
                    free = available.data.get("free", [])
                    if free:
                        inline_kb = []
                        row = []
                        for n in free:
                            row.append({"text": str(n), "callback_data": f"/claim {n}"})
                            if len(row) == 5:
                                inline_kb.append(row)
                                row = []
                        if row:
                            inline_kb.append(row)
                        if lang == "fa":
                            reply = "لطفا یک بخش را برای دریافت انتخاب کنید:"
                        elif lang == "ar":
                            reply = "الرجاء اختيار جزء:"
                        else:
                            reply = "Please select a portion to claim:"
                    else:
                        if lang == "fa":
                            reply = "هیچ بخش آزادی برای رزرو وجود ندارد."
                        elif lang == "ar":
                            reply = "لا توجد أجزاء متاحة للحجز."
                        else:
                            reply = "There are no free portions available to claim."

            elif parsed and parsed.action == "done" and not parsed.args:
                member = svc.get_or_create_member(group, f"tg:{user_id}")
                mine_res = svc.mine(group, member)
                if mine_res.ok:
                    claims = mine_res.data.get("claims", [])
                    active_claims = [c for c in claims if c.status != "done"]
                    if active_claims:
                        inline_kb = []
                        row = []
                        for c in active_claims:
                            row.append({"text": str(c.portion_number), "callback_data": f"/done {c.portion_number}"})
                            if len(row) == 5:
                                inline_kb.append(row)
                                row = []
                        if row:
                            inline_kb.append(row)
                        if lang == "fa":
                            reply = "کدام بخش را به اتمام رسانده‌اید؟"
                        elif lang == "ar":
                            reply = "أي جزء أتممت؟"
                        else:
                            reply = "Which portion have you completed?"
                    else:
                        if lang == "fa":
                            reply = "شما هیچ بخش رزرو شده‌ای ندارید."
                        elif lang == "ar":
                            reply = "ليس لديك أجزاء محجوزة."
                        else:
                            reply = "You don't have any claimed portions."

            from src.i18n import t
            if reply in (t("en", "claim_no_cycle"), t("fa", "claim_no_cycle"), t("ar", "claim_no_cycle")):
                is_admin = svc.is_admin(group, f"tg:{user_id}")
                if is_admin:
                    btn_text = "Start Cycle"
                    if lang == "fa": btn_text = "شروع دوره"
                    elif lang == "ar": btn_text = "دورة جديدة"
                    inline_kb = [[{"text": btn_text, "callback_data": "/startcycle"}]]

            elif parsed and parsed.action == "startcycle":
                btn_text = "Claim"
                if lang == "fa": btn_text = "رزرو"
                elif lang == "ar": btn_text = "حجز"
                inline_kb = [[{"text": btn_text, "callback_data": "/claim"}]]

            elif parsed and parsed.action == "settings":
                is_admin = svc.is_admin(group, f"tg:{user_id}")
                if is_admin:
                    inline_kb = [
                        [{"text": "Change Unit", "callback_data": "/tg_settings unit"}, {"text": "Change Cycle", "callback_data": "/tg_settings cycle"}],
                        [{"text": "Change Reminders", "callback_data": "/tg_settings rem"}, {"text": "Change Ads", "callback_data": "/tg_settings ads"}]
                    ]

            reply_markup = {"inline_keyboard": inline_kb} if inline_kb else {"keyboard": kb, "resize_keyboard": True}

            return {
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": reply,
                "parse_mode": "Markdown",
                "reply_markup": reply_markup
            }
    except Exception as e:
        logger.exception("Failed handling message from telegram user %s", user_id)
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": f"Error: {repr(e)}",
        }

    return {"status": "ok"}
