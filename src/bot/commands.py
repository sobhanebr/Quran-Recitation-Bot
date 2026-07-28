"""Command parsing with English / Persian / Arabic aliases."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# Map normalized command tokens -> canonical action
ALIASES: dict[str, str] = {
    # help
    "help": "help",
    "راهنما": "help",
    "مساعدة": "help",
    "مساعده": "help",
    # language
    "lang": "lang",
    "language": "lang",
    "زبان": "lang",
    "لغة": "lang",
    # status
    "status": "status",
    "وضعیت": "status",
    "وضعيت": "status",
    "حالة": "status",
    "حاله": "status",
    # available
    "available": "available",
    "free": "available",
    "آزاد": "available",
    "متاح": "available",
    # claim
    "claim": "claim",
    "رزرو": "claim",
    "حجز": "claim",
    "take": "claim",
    # release
    "release": "release",
    "آزادسازی": "release",
    "ازادسازي": "release",
    "إلغاء": "release",
    "الغاء": "release",
    # done
    "done": "done",
    "تمام": "done",
    "تم": "done",
    "complete": "done",
    # mine
    "mine": "mine",
    "من": "mine",
    "لي": "mine",
    "my": "mine",
    # start cycle (was: start week)
    "startcycle": "startcycle",
    "newcycle": "startcycle",
    "startweek": "startcycle",
    "newweek": "startcycle",
    "هفته‌جدید": "startcycle",
    "هفتهجدید": "startcycle",
    "هفته-جدید": "startcycle",
    "هفته جديد": "startcycle",
    "دورهجدید": "startcycle",
    "دوره‌جدید": "startcycle",
    "دوره-جدید": "startcycle",
    "أسبوع-جديد": "startcycle",
    "اسبوع-جديد": "startcycle",
    "أسبوعجديد": "startcycle",
    "دورة-جديدة": "startcycle",
    "دورةجديدة": "startcycle",
    # granularity
    "granularity": "granularity",
    "unit": "granularity",
    "واحد": "granularity",
    "وحدة": "granularity",
    "وحده": "granularity",
    # cycle length
    "cycle": "cycle",
    "دوره": "cycle",
    "دورة": "cycle",
    # reminders
    "reminders": "reminders",
    "reminder": "reminders",
    "یادآوری": "reminders",
    "يادآوري": "reminders",
    "تذكير": "reminders",
    "تذکیر": "reminders",
    # advertise open spots
    "advertise": "advertise",
    "ads": "advertise",
    "اعلان": "advertise",
    "إعلان": "advertise",
    "تبلیغ": "advertise",
    # personal plan
    "plan": "plan",
    "برنامه": "plan",
    "خطة": "plan",
    "خطه": "plan",
    # settings
    "settings": "settings",
    "تنظیمات": "settings",
    "تنظيمات": "settings",
    "إعدادات": "settings",
    "اعدادات": "settings",
    # niyyah
    "niyyah": "niyyah",
    "niyah": "niyyah",
    "intention": "niyyah",
    "نیت": "niyyah",
    "نيت": "niyyah",
    "نية": "niyyah",
    # admin
    "admin": "admin",
    "admins": "admins",
    "مدیران": "admins",
    "المشرفون": "admins",
}


@dataclass
class ParsedCommand:
    action: str
    args: list[str]
    raw: str


_CMD_RE = re.compile(
    r"^[/!.]?\s*(?P<cmd>[^\s]+)\s*(?P<rest>.*)$",
    re.UNICODE | re.DOTALL,
)


def _normalize_token(token: str) -> str:
    t = token.strip().lstrip("/!.")
    # collapse zero-width / tatweel
    t = t.replace("\u200c", "").replace("\u0640", "")
    return t.lower() if t.isascii() else t


def parse_command(text: str) -> Optional[ParsedCommand]:
    if not text or not text.strip():
        return None
    cleaned = text.strip()
    # Ignore plain chat that doesn't look like a command
    if not cleaned.startswith(("/", "!", ".")) and cleaned.split()[0].lower() not in ALIASES:
        # Allow bare Persian/Arabic command words without slash
        first = cleaned.split()[0]
        if _normalize_token(first) not in ALIASES and first not in ALIASES:
            return None

    m = _CMD_RE.match(cleaned)
    if not m:
        return None
    raw_cmd = m.group("cmd")
    rest = (m.group("rest") or "").strip()
    token = _normalize_token(raw_cmd)
    # Also try original (for non-lowercased Arabic/Persian keys)
    action = ALIASES.get(token) or ALIASES.get(raw_cmd.lstrip("/!."))
    if not action:
        # try without lower for FA/AR
        action = ALIASES.get(raw_cmd.lstrip("/!."))
    if not action:
        return ParsedCommand(action="unknown", args=[], raw=cleaned)

    args = rest.split() if rest else []
    # For niyyah, keep full remainder as a single arg when present
    if action == "niyyah" and rest:
        args = [rest]
    return ParsedCommand(action=action, args=args, raw=cleaned)


def parse_number(arg: str | None) -> Optional[int]:
    if arg is None:
        return None
    # Eastern Arabic / Persian digits
    trans = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
    s = arg.strip().translate(trans)
    if not s.isdigit():
        return None
    return int(s)


# Backwards-compatible alias
parse_juz = parse_number
