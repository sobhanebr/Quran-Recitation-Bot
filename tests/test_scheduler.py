"""Tests for the scheduler tick due-logic (pure, no real scheduler)."""

from datetime import datetime, timedelta, timezone

from src.bot.handlers import handle_message
from src.services.scheduler_service import collect_due_messages


def _msg(db, text, user="111", chat="group-1", name="Ali"):
    return handle_message(db, chat_id=chat, user_id=user, display_name=name, text=text)


NOW = datetime(2026, 7, 12, 12, 0, tzinfo=timezone.utc)


def test_no_messages_when_nothing_due(db_session):
    _msg(db_session, "/help", user="admin1")
    _msg(db_session, "/reminders off", user="admin1")
    _msg(db_session, "/startcycle", user="admin1")
    outbox = collect_due_messages(db_session, now=datetime.now(timezone.utc))
    assert outbox == []


def test_reminder_sent_to_members_with_pending_claims(db_session):
    _msg(db_session, "/help", user="admin1")
    _msg(db_session, "/startcycle", user="admin1")
    _msg(db_session, "/claim 1", user="u1", name="Sara")
    _msg(db_session, "/claim 2", user="u2", name="Omar")
    _msg(db_session, "/done 2", user="u2", name="Omar")

    # Default reminders: daily. One day later a reminder is due for u1 only.
    later = datetime.now(timezone.utc) + timedelta(days=1, minutes=1)
    outbox = collect_due_messages(db_session, now=later)
    recipients = [to for to, _ in outbox]
    assert "u1" in recipients
    assert "u2" not in recipients

    # Not due again immediately after
    outbox2 = collect_due_messages(db_session, now=later + timedelta(minutes=5))
    assert all(to != "u1" for to, _ in outbox2)


def test_ads_broadcast_open_spots(db_session):
    _msg(db_session, "/help", user="admin1")
    _msg(db_session, "/reminders off", user="admin1")
    _msg(db_session, "/advertise daily", user="admin1")
    _msg(db_session, "/startcycle", user="admin1")
    _msg(db_session, "/claim 1", user="u1", name="Sara")

    later = datetime.now(timezone.utc) + timedelta(days=1, minutes=1)
    outbox = collect_due_messages(db_session, now=later)
    # All members (admin1 and u1) get the announcement
    recipients = sorted(to for to, _ in outbox)
    assert recipients == ["admin1", "u1"]
    body = outbox[0][1]
    assert "2" in body  # portion 2 is free
    assert "/claim" in body or "حجز" in body


def test_cycle_rollover_announced(db_session):
    _msg(db_session, "/help", user="admin1")
    _msg(db_session, "/reminders off", user="admin1")
    _msg(db_session, "/cycle daily", user="admin1")
    _msg(db_session, "/startcycle", user="admin1")

    from src.services.group_service import QuranGroupService

    svc = QuranGroupService(db_session)
    group = svc.get_or_create_group("group-1")
    first = svc.current_cycle(group)
    assert first.cycle_number == 1

    later = datetime.now(timezone.utc) + timedelta(days=2)
    outbox = collect_due_messages(db_session, now=later)
    new_cycle = svc.current_cycle(group)
    assert new_cycle.cycle_number == 2
    assert any("#2" in body for _, body in outbox)


def test_personal_plan_checkin(db_session):
    _msg(db_session, "/plan start 1 juz daily", user="p1", chat="dm-p1")
    later = datetime.now(timezone.utc) + timedelta(days=1, minutes=1)
    outbox = collect_due_messages(db_session, now=later)
    assert any(
        to == "p1" and "Juz 1" in body and "https://quran.com/juz/1" in body
        for to, body in outbox
    )

    # Immediately after, nothing more is due for the plan
    outbox2 = collect_due_messages(db_session, now=later + timedelta(minutes=1))
    assert all(to != "p1" for to, _ in outbox2)
