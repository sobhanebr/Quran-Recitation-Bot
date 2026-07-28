"""Periodic tick: cycle rollover, reminders, open-spot ads, and plan check-ins.

State lives on the rows themselves (``ends_at`` / ``last_*_at``), so the tick
is restart-safe and needs no persistent job store.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.i18n import t, unit_label
from src.models.entities import Group, Member, PersonalPlan, PortionClaim
from src.quran_meta import interval_delta, portion_url
from src.services.group_service import QuranGroupService
from src.services.plan_service import portion_range

logger = logging.getLogger(__name__)

MAX_LISTED_PORTIONS = 40


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    """SQLite returns naive datetimes; treat them as UTC."""
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def _interval_due(last: datetime | None, base: datetime | None, spec: str, now: datetime) -> bool:
    delta = interval_delta(spec)
    if delta is None:
        return False
    anchor = _aware(last) or _aware(base)
    if anchor is None:
        return True
    return now >= anchor + delta


def _compact_numbers(numbers: list[int]) -> str:
    shown = numbers[:MAX_LISTED_PORTIONS]
    text = " ".join(str(n) for n in shown)
    if len(numbers) > MAX_LISTED_PORTIONS:
        text += " …"
    return text


def collect_due_messages(db: Session, now: datetime | None = None) -> list[tuple[str, str]]:
    """Advance due state and return (recipient_wa_id, body) pairs to send."""
    now = now or _utcnow()
    svc = QuranGroupService(db)
    outbox: list[tuple[str, str]] = []

    for group in db.scalars(select(Group)).all():
        lang = group.language
        cycle = svc.current_cycle(group)

        # 1) Auto-roll expired cycles
        if cycle and _aware(cycle.ends_at) and _aware(cycle.ends_at) <= now:
            result = svc.start_cycle(group)
            cycle = result.data["cycle"]
            body = t(
                lang,
                "cycle_rollover",
                cycle=cycle.cycle_number,
                total=svc.cycle_total(cycle),
                unit=unit_label(lang, cycle.granularity),
            )
            for m in group.members:
                outbox.append((m.wa_user_id, body))

        if not cycle:
            continue
        unit = unit_label(lang, cycle.granularity)

        # 2) Completion reminders for members with pending claims
        if _interval_due(group.last_reminder_at, cycle.started_at, group.reminder_spec, now):
            pending = db.scalars(
                select(PortionClaim)
                .join(Member)
                .where(PortionClaim.cycle_id == cycle.id, PortionClaim.status != "done")
                .order_by(PortionClaim.portion_number)
            ).all()
            by_member: dict[int, list[PortionClaim]] = {}
            for c in pending:
                by_member.setdefault(c.member_id, []).append(c)
            for claims in by_member.values():
                member = claims[0].member
                lines = "\n".join(
                    t(
                        lang,
                        "reminder_line",
                        unit=unit,
                        num=c.portion_number,
                        link=portion_url(cycle.granularity, c.portion_number),
                    )
                    for c in claims
                )
                outbox.append((member.wa_user_id, t(lang, "reminder_message", lines=lines)))
            group.last_reminder_at = now
            db.commit()

        # 3) Open-spot announcements
        if _interval_due(group.last_ad_at, cycle.started_at, group.ad_spec, now):
            avail = svc.available_portions(group)
            free = avail.data.get("free", []) if avail.ok else []
            if free:
                body = t(
                    lang,
                    "ad_message",
                    count=len(free),
                    lines=_compact_numbers(free),
                )
                for m in group.members:
                    outbox.append((m.wa_user_id, body))
            group.last_ad_at = now
            db.commit()

    # 4) Personal plan check-ins
    plans = db.scalars(select(PersonalPlan).where(PersonalPlan.active.is_(True))).all()
    for plan in plans:
        if not _interval_due(plan.last_reminder_at, plan.started_at, plan.cycle_spec, now):
            continue
        start, end = portion_range(plan)
        range_str = str(start) if start == end else f"{start}-{end}"
        body = t(
            plan.language,
            "plan_checkin",
            unit=unit_label(plan.language, plan.granularity),
            range=range_str,
            link=portion_url(plan.granularity, start),
        )
        outbox.append((plan.wa_user_id, body))
        plan.last_reminder_at = now
        db.commit()

    return outbox


async def run_tick() -> None:
    """Entry point for the APScheduler job."""
    from src.api.telegram_client import TelegramClient
    from src.api.whatsapp_client import WhatsAppClient
    from src.models.db import SessionLocal

    wa_client = WhatsAppClient()
    tg_client = TelegramClient()
    db = SessionLocal()
    try:
        outbox = collect_due_messages(db)
    except Exception:
        logger.exception("Scheduler tick failed")
        return
    finally:
        db.close()

    for to, body in outbox:
        try:
            if to.startswith("tg:"):
                await tg_client.send_text(to[3:], body)
            else:
                await wa_client.send_text(to, body)
        except Exception:
            logger.exception("Failed to send scheduled message to %s", to)
