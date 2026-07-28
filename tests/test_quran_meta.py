from datetime import timedelta

from src.quran_meta import (
    cycle_delta,
    interval_delta,
    parse_cycle_spec,
    parse_granularity,
    parse_interval_spec,
    portion_url,
    total_portions,
)


def test_parse_granularity_aliases():
    assert parse_granularity("juz") == "juz"
    assert parse_granularity("جزء") == "juz"
    assert parse_granularity("Page") == "page"
    assert parse_granularity("صفحه") == "page"
    assert parse_granularity("سورة") == "surah"
    assert parse_granularity("hizb") == "hizb"
    assert parse_granularity("quran") == "quran"
    assert parse_granularity("bogus") is None
    assert parse_granularity(None) is None


def test_total_portions():
    assert total_portions("page") == 604
    assert total_portions("surah") == 114
    assert total_portions("hizb") == 60
    assert total_portions("juz") == 30
    assert total_portions("quran") == 1


def test_portion_url():
    assert portion_url("page", 302) == "https://quran.com/page/302"
    assert portion_url("surah", 36) == "https://quran.com/36"
    assert portion_url("hizb", 12) == "https://quran.com/hizb/12"
    assert portion_url("juz", 5) == "https://quran.com/juz/5"
    assert portion_url("quran", 1) == "https://quran.com"


def test_parse_cycle_spec():
    assert parse_cycle_spec("daily") == "daily"
    assert parse_cycle_spec("weekly") == "weekly"
    assert parse_cycle_spec("monthly") == "monthly"
    assert parse_cycle_spec("روزانه") == "daily"
    assert parse_cycle_spec("شهري") == "monthly"
    assert parse_cycle_spec("10d") == "10d"
    assert parse_cycle_spec("۱۰d") == "10d"
    assert parse_cycle_spec("0d") is None
    assert parse_cycle_spec("5h") is None  # hours not valid for cycles
    assert parse_cycle_spec("nonsense") is None


def test_cycle_delta():
    assert cycle_delta("daily") == timedelta(days=1)
    assert cycle_delta("weekly") == timedelta(weeks=1)
    assert cycle_delta("monthly") == timedelta(days=30)
    assert cycle_delta("10d") == timedelta(days=10)


def test_parse_interval_spec():
    assert parse_interval_spec("off") == "off"
    assert parse_interval_spec("خاموش") == "off"
    assert parse_interval_spec("daily") == "daily"
    assert parse_interval_spec("weekly") == "weekly"
    assert parse_interval_spec("6h") == "6h"
    assert parse_interval_spec("3d") == "3d"
    assert parse_interval_spec("monthly") is None
    assert parse_interval_spec("garbage") is None


def test_interval_delta():
    assert interval_delta("off") is None
    assert interval_delta("daily") == timedelta(days=1)
    assert interval_delta("6h") == timedelta(hours=6)
    assert interval_delta("3d") == timedelta(days=3)
