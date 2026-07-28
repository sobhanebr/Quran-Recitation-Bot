"""Tests for granularity, cycle length, reminders, ads, settings, and personal plans."""

from src.bot.handlers import handle_message


def _msg(db, text, user="111", chat="group-1", name="Ali"):
    return handle_message(
        db,
        chat_id=chat,
        user_id=user,
        display_name=name,
        text=text,
    )


def _bootstrap(db, user="admin1"):
    _msg(db, "/help", user=user)


def test_granularity_change(db_session):
    _bootstrap(db_session)
    reply = _msg(db_session, "/granularity hizb", user="admin1")
    assert "Hizb" in reply and "60" in reply

    start = _msg(db_session, "/startcycle", user="admin1")
    assert "60" in start

    claim = _msg(db_session, "/claim 45", user="u1")
    assert "45" in claim

    bad = _msg(db_session, "/claim 61", user="u1")
    assert "60" in bad


def test_granularity_admin_only_and_invalid(db_session):
    _bootstrap(db_session)
    denied = _msg(db_session, "/granularity page", user="not-admin")
    assert "admin" in denied.lower()
    invalid = _msg(db_session, "/granularity bogus", user="admin1")
    assert "granularity" in invalid.lower() or "Usage" in invalid


def test_granularity_applies_next_cycle(db_session):
    _bootstrap(db_session)
    _msg(db_session, "/startcycle", user="admin1")
    _msg(db_session, "/granularity page", user="admin1")
    # Current cycle still runs on juz (30)
    bad = _msg(db_session, "/claim 100", user="u1")
    assert "30" in bad
    _msg(db_session, "/startcycle", user="admin1")
    ok = _msg(db_session, "/claim 100", user="u1")
    assert "100" in ok


def test_cycle_spec_command(db_session):
    _bootstrap(db_session)
    reply = _msg(db_session, "/cycle monthly", user="admin1")
    assert "monthly" in reply
    reply = _msg(db_session, "/cycle 10d", user="admin1")
    assert "10d" in reply
    invalid = _msg(db_session, "/cycle sometimes", user="admin1")
    assert "daily" in invalid


def test_cycle_sets_ends_at(db_session):
    from src.services.group_service import QuranGroupService

    _bootstrap(db_session)
    _msg(db_session, "/cycle daily", user="admin1")
    _msg(db_session, "/startcycle", user="admin1")
    svc = QuranGroupService(db_session)
    group = svc.get_or_create_group("group-1")
    cycle = svc.current_cycle(group)
    assert cycle.ends_at is not None
    assert (cycle.ends_at - cycle.started_at).days == 1


def test_reminders_and_advertise_commands(db_session):
    _bootstrap(db_session)
    on = _msg(db_session, "/reminders 6h", user="admin1")
    assert "6h" in on
    off = _msg(db_session, "/reminders off", user="admin1")
    assert "off" in off.lower()

    ads_on = _msg(db_session, "/advertise daily", user="admin1")
    assert "daily" in ads_on
    ads_off = _msg(db_session, "/advertise off", user="admin1")
    assert "off" in ads_off.lower()

    denied = _msg(db_session, "/reminders daily", user="u9")
    assert "admin" in denied.lower()


def test_settings_overview(db_session):
    _bootstrap(db_session)
    _msg(db_session, "/granularity surah", user="admin1")
    _msg(db_session, "/cycle monthly", user="admin1")
    reply = _msg(db_session, "/settings", user="u1")
    assert "Surah" in reply
    assert "114" in reply
    assert "monthly" in reply


def test_startweek_alias_still_works(db_session):
    _bootstrap(db_session)
    start = _msg(db_session, "/startweek", user="admin1")
    assert "#" in start


def test_claim_reply_includes_quran_link(db_session):
    _bootstrap(db_session)
    _msg(db_session, "/granularity hizb", user="admin1")
    _msg(db_session, "/startcycle", user="admin1")
    reply = _msg(db_session, "/claim 12", user="u1")
    assert "https://quran.com/hizb/12" in reply


def test_personal_plan_flow(db_session):
    started = _msg(db_session, "/plan start 2 juz daily", user="p1", chat="dm-p1")
    assert "2" in started and "1-2" in started
    assert "https://quran.com/juz/1" in started

    status = _msg(db_session, "/plan status", user="p1", chat="dm-p1")
    assert "0/30" in status

    done = _msg(db_session, "/plan done", user="p1", chat="dm-p1")
    assert "3-4" in done

    status2 = _msg(db_session, "/plan status", user="p1", chat="dm-p1")
    assert "2/30" in status2

    stopped = _msg(db_session, "/plan stop", user="p1", chat="dm-p1")
    assert "stopped" in stopped.lower()

    none_left = _msg(db_session, "/plan status", user="p1", chat="dm-p1")
    assert "No active" in none_left


def test_personal_plan_khatm_completion(db_session):
    _msg(db_session, "/plan start 1 quran daily", user="p2", chat="dm-p2")
    done = _msg(db_session, "/plan done", user="p2", chat="dm-p2")
    assert "khatm" in done.lower()
    # Plan restarts from position 1
    status = _msg(db_session, "/plan status", user="p2", chat="dm-p2")
    assert "0/1" in status


def test_plan_usage_on_bad_subcommand(db_session):
    reply = _msg(db_session, "/plan whatever", user="p3", chat="dm-p3")
    assert "/plan start" in reply
