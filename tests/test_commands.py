from src.bot.commands import parse_command, parse_juz
from src.i18n import normalize_lang, t


def test_parse_english_claim():
    cmd = parse_command("/claim 7")
    assert cmd is not None
    assert cmd.action == "claim"
    assert cmd.args == ["7"]


def test_parse_persian_claim():
    cmd = parse_command("/رزرو ۱۲")
    assert cmd is not None
    assert cmd.action == "claim"
    assert parse_juz(cmd.args[0]) == 12


def test_parse_arabic_done():
    cmd = parse_command("تم 3")
    assert cmd is not None
    assert cmd.action == "done"
    assert parse_juz(cmd.args[0]) == 3


def test_parse_niyyah_keeps_text():
    cmd = parse_command("/نیت شفای بیماران گروه")
    assert cmd is not None
    assert cmd.action == "niyyah"
    assert cmd.args == ["شفای بیماران گروه"]


def test_parse_ignores_plain_chat():
    assert parse_command("salam everyone") is None


def test_eastern_digits():
    assert parse_juz("٣٠") == 30
    assert parse_juz("۱۵") == 15


def test_i18n_langs():
    link = "https://quran.com/juz/1"
    assert "Juz" in t("en", "claim_ok", unit="Juz", num=1, link=link)
    assert "جزء" in t("fa", "claim_ok", unit="جزء", num=1, link=link)
    assert "الجزء" in t("ar", "claim_ok", unit="الجزء", num=1, link=link)
    assert normalize_lang("فارسی") == "fa"
    assert normalize_lang("arabic") == "ar"
