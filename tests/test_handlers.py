from src.bot.handlers import handle_message


def _msg(db, text, user="111", chat="group-1", name="Ali"):
    return handle_message(
        db,
        chat_id=chat,
        user_id=user,
        display_name=name,
        text=text,
    )


def test_full_week_flow_english(db_session):
    # First user becomes admin when group has none
    help_reply = _msg(db_session, "/help")
    assert help_reply
    assert "Admin" in help_reply or "admin" in help_reply.lower() or "Juz" in help_reply

    start = _msg(db_session, "/startweek")
    assert "week" in start.lower() or "#" in start

    niyyah = _msg(db_session, "/niyyah For the ummah")
    assert "For the ummah" in niyyah

    claim = _msg(db_session, "/claim 1", user="222", name="Sara")
    assert "1" in claim

    taken = _msg(db_session, "/claim 1", user="333", name="Omar")
    assert "Sara" in taken or "already" in taken.lower()

    avail = _msg(db_session, "/available")
    assert "Available" in avail
    # Juz 1 claimed — remaining list should still mention other numbers
    assert "2" in avail
    assert "30" in avail

    done = _msg(db_session, "/done 1", user="222", name="Sara")
    assert "done" in done.lower() or "جزاكم" in done

    status = _msg(db_session, "/status")
    assert "For the ummah" in status
    assert "Sara" in status


def test_persian_flow(db_session):
    _msg(db_session, "/help", user="admin1")
    lang = _msg(db_session, "/lang fa", user="admin1")
    assert "فارسی" in lang

    start = _msg(db_session, "/هفته‌جدید", user="admin1")
    assert "دوره" in start

    niyyah = _msg(db_session, "/نیت شفای بیماران", user="admin1")
    assert "شفای بیماران" in niyyah

    claim = _msg(db_session, "/رزرو ۵", user="m1", name="مریم")
    assert "۵" in claim or "5" in claim

    status = _msg(db_session, "/وضعیت", user="m1", name="مریم")
    assert "نیت" in status
    assert "مریم" in status


def test_arabic_claim_alias(db_session):
    _msg(db_session, "/help", user="a1")
    _msg(db_session, "/lang ar", user="a1")
    _msg(db_session, "/startweek", user="a1")
    reply = _msg(db_session, "/حجز 10", user="u2", name="أحمد")
    assert "10" in reply


def test_release_and_mine(db_session):
    _msg(db_session, "/help", user="a1")
    _msg(db_session, "/startweek", user="a1")
    _msg(db_session, "/claim 3", user="u1", name="Bob")
    mine = _msg(db_session, "/mine", user="u1", name="Bob")
    assert "3" in mine
    released = _msg(db_session, "/release 3", user="u1", name="Bob")
    assert "3" in released
    mine2 = _msg(db_session, "/mine", user="u1", name="Bob")
    assert "no Juz" in mine2 or "no" in mine2.lower()


def test_admin_only_niyyah(db_session):
    _msg(db_session, "/help", user="a1")
    _msg(db_session, "/startweek", user="a1")
    denied = _msg(db_session, "/niyyah secret", user="u9", name="Nope")
    assert "admin" in denied.lower()


def test_invalid_juz(db_session):
    _msg(db_session, "/help", user="a1")
    _msg(db_session, "/startweek", user="a1")
    bad = _msg(db_session, "/claim 99", user="a1")
    assert "1" in bad and "30" in bad
