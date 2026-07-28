"""Quran structure metadata and schedule-spec parsing.

Granularities map to the number of portions in a full khatm.
Cycle specs describe how long a group cycle lasts; interval specs
describe how often recurring messages (reminders / ads) fire.
"""

from __future__ import annotations

import re
from datetime import timedelta
from typing import Optional

# Granularity -> total number of portions in the whole Quran
GRANULARITIES: dict[str, int] = {
    "page": 604,
    "surah": 114,
    "hizb": 60,
    "juz": 30,
    "quran": 1,
}

DEFAULT_GRANULARITY = "juz"
DEFAULT_CYCLE_SPEC = "weekly"
DEFAULT_REMINDER_SPEC = "daily"
DEFAULT_AD_SPEC = "off"

_GRANULARITY_ALIASES: dict[str, str] = {
    "page": "page",
    "pages": "page",
    "صفحه": "page",
    "صفحة": "page",
    "surah": "surah",
    "sura": "surah",
    "سوره": "surah",
    "سورة": "surah",
    "hizb": "hizb",
    "حزب": "hizb",
    "juz": "juz",
    "juz'": "juz",
    "جزء": "juz",
    "جز": "juz",
    "quran": "quran",
    "whole": "quran",
    "قرآن": "quran",
    "قران": "quran",
    "ختم": "quran",
}

_CYCLE_WORDS: dict[str, str] = {
    "daily": "daily",
    "day": "daily",
    "روزانه": "daily",
    "يومي": "daily",
    "یومی": "daily",
    "weekly": "weekly",
    "week": "weekly",
    "هفتگی": "weekly",
    "أسبوعي": "weekly",
    "اسبوعي": "weekly",
    "monthly": "monthly",
    "month": "monthly",
    "ماهانه": "monthly",
    "شهري": "monthly",
    "شهری": "monthly",
    "off": "off",
    "none": "off",
    "خاموش": "off",
    "إيقاف": "off",
    "ايقاف": "off",
}

_DIGIT_TRANS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

_CUSTOM_RE = re.compile(r"^(\d+)\s*([hd])$")


def _normalize(token: str) -> str:
    t = token.strip().translate(_DIGIT_TRANS)
    t = t.replace("\u200c", "").replace("\u0640", "")
    return t.lower() if t.isascii() else t


def parse_granularity(token: str | None) -> Optional[str]:
    """Return canonical granularity name or None."""
    if not token:
        return None
    return _GRANULARITY_ALIASES.get(_normalize(token))


def total_portions(granularity: str) -> int:
    return GRANULARITIES.get(granularity, GRANULARITIES[DEFAULT_GRANULARITY])


_QURAN_COM = "https://quran.com"

_URL_PATTERNS: dict[str, str] = {
    "page": _QURAN_COM + "/page/{n}",
    "surah": _QURAN_COM + "/{n}",
    "hizb": _QURAN_COM + "/hizb/{n}",
    "juz": _QURAN_COM + "/juz/{n}",
    "quran": _QURAN_COM,
}


def portion_url(granularity: str, n: int) -> str:
    """Deep link to the portion on quran.com (numbering matches ours 1:1)."""
    pattern = _URL_PATTERNS.get(granularity, _URL_PATTERNS[DEFAULT_GRANULARITY])
    return pattern.format(n=n)


def parse_cycle_spec(token: str | None) -> Optional[str]:
    """Parse a cycle length: daily | weekly | monthly | <N>d. Returns normalized spec."""
    if not token:
        return None
    t = _normalize(token)
    word = _CYCLE_WORDS.get(t)
    if word in ("daily", "weekly", "monthly"):
        return word
    m = _CUSTOM_RE.match(t)
    if m and m.group(2) == "d" and int(m.group(1)) > 0:
        return f"{int(m.group(1))}d"
    return None


def cycle_delta(spec: str) -> timedelta:
    if spec == "daily":
        return timedelta(days=1)
    if spec == "weekly":
        return timedelta(weeks=1)
    if spec == "monthly":
        return timedelta(days=30)
    m = _CUSTOM_RE.match(spec)
    if m and m.group(2) == "d":
        return timedelta(days=int(m.group(1)))
    return timedelta(weeks=1)


def parse_interval_spec(token: str | None) -> Optional[str]:
    """Parse a recurring interval: off | daily | weekly | <N>h | <N>d."""
    if not token:
        return None
    t = _normalize(token)
    word = _CYCLE_WORDS.get(t)
    if word in ("off", "daily", "weekly"):
        return word
    m = _CUSTOM_RE.match(t)
    if m and int(m.group(1)) > 0:
        return f"{int(m.group(1))}{m.group(2)}"
    return None


def interval_delta(spec: str) -> Optional[timedelta]:
    """None means the interval is disabled."""
    if not spec or spec == "off":
        return None
    if spec == "daily":
        return timedelta(days=1)
    if spec == "weekly":
        return timedelta(weeks=1)
    m = _CUSTOM_RE.match(spec)
    if m:
        n = int(m.group(1))
        return timedelta(hours=n) if m.group(2) == "h" else timedelta(days=n)
    return None
