"""Message handlers: route commands to domain services and format replies."""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.bot.commands import parse_command, parse_number
from src.i18n import normalize_lang, t, unit_label
from src.quran_meta import (
    parse_cycle_spec,
    parse_granularity,
    parse_interval_spec,
    portion_url,
    total_portions,
)
from src.services.group_service import QuranGroupService
from src.services.plan_service import PersonalPlanService


def format_range(start: int, end: int) -> str:
    return str(start) if start == end else f"{start}-{end}"


def _format_available(lang: str, unit: str, total: int, free: list[int]) -> str:
    if not free:
        return t(lang, "available_none", total=total)
    header = t(lang, "available_header", unit=unit, count=len(free), total=total)
    # Compact rows for readability
    chunks: list[str] = []
    row: list[str] = []
    for i, n in enumerate(free, 1):
        row.append(str(n))
        if i % 10 == 0:
            chunks.append(" ".join(row))
            row = []
    if row:
        chunks.append(" ".join(row))
    return header + "\n" + "\n".join(chunks)


def _status_label(lang: str, status: str) -> str:
    return t(lang, "status_done" if status == "done" else "status_claimed")


def _format_status(lang: str, unit: str, data: dict) -> str:
    cycle = data["cycle"]
    lines = [
        t(
            lang,
            "status_header",
            cycle=cycle.cycle_number,
            claimed=data["claimed"],
            done=data["done"],
            free=data["free"],
        )
    ]
    if cycle.niyyah:
        lines.append(t(lang, "status_niyyah", niyyah=cycle.niyyah))
    claims = data["claims"]
    if not claims:
        lines.append(t(lang, "status_empty", total=data["total"]))
    else:
        claim_lines = []
        for c in claims:
            name = c.member.display_name or c.member.wa_user_id
            claim_lines.append(
                t(lang, "claim_line", unit=unit, num=c.portion_number, name=name, status=_status_label(lang, c.status))
            )
        lines.append(t(lang, "status_claims", lines="\n".join(claim_lines)))
    return "\n".join(lines)


def _format_mine(lang: str, unit: str, claims) -> str:
    if not claims:
        return t(lang, "mine_empty")
    claim_lines = [
        t(lang, "claim_line", unit=unit, num=c.portion_number, name="✓", status=_status_label(lang, c.status))
        for c in claims
    ]
    return t(lang, "mine_header", lines="\n".join(claim_lines))


def _handle_plan(
    db: Session, *, user_id: str, display_name: str, lang: str, args: list[str]
) -> str:
    """Personal recitation plan sub-commands: start / status / done / stop."""
    plans = PersonalPlanService(db)
    sub = (args[0].lower() if args else "").strip()

    def plan_reply(result) -> str:
        plan = (result.data or {}).get("plan")
        params = dict(result.params)
        if plan is not None:
            params.setdefault("unit", unit_label(lang, plan.granularity))
            if "start" in params and "end" in params:
                params.setdefault("link", portion_url(plan.granularity, params["start"]))
                params["range"] = format_range(params.pop("start"), params.pop("end"))
        return t(lang, result.key, **params)

    if sub in ("status", "وضعیت", "حالة"):
        return plan_reply(plans.plan_status(user_id))
    if sub in ("done", "تمام", "تم"):
        return plan_reply(plans.mark_done(user_id))
    if sub in ("stop", "توقف", "إيقاف", "ایست"):
        return plan_reply(plans.stop_plan(user_id))
    if sub in ("start", "شروع", "بدء"):
        rest = args[1:]
        count = 1
        granularity = None
        cycle_spec = None
        for token in rest:
            n = parse_number(token)
            if n is not None:
                count = n
                continue
            g = parse_granularity(token)
            if g is not None:
                granularity = g
                continue
            c = parse_cycle_spec(token)
            if c is not None:
                cycle_spec = c
        granularity = granularity or "juz"
        cycle_spec = cycle_spec or "daily"
        if count < 1:
            return t(lang, "plan_usage")
        result = plans.start_plan(
            user_id,
            display_name=display_name,
            language=lang,
            granularity=granularity,
            units_per_cycle=count,
            cycle_spec=cycle_spec,
        )
        return plan_reply(result)
    return t(lang, "plan_usage")


def handle_message(
    db: Session,
    *,
    chat_id: str,
    user_id: str,
    display_name: str,
    text: str,
    chat_title: str | None = None,
) -> str | None:
    """Process inbound text. Returns reply text, or None if message should be ignored."""
    parsed = parse_command(text)
    if not parsed:
        return None

    svc = QuranGroupService(db)
    group = svc.get_or_create_group(chat_id, title=chat_title)
    member = svc.get_or_create_member(group, user_id, display_name=display_name)
    bootstrapped = svc.ensure_bootstrap_admin(group, user_id)
    lang = group.language
    action = parsed.action
    args = parsed.args

    def current_unit_and_total() -> tuple[str, int]:
        cycle = svc.current_cycle(group)
        granularity = cycle.granularity if cycle else group.granularity
        return unit_label(lang, granularity), total_portions(granularity)

    def reply(key: str, **params) -> str:
        cycle = svc.current_cycle(group)
        granularity = cycle.granularity if cycle else group.granularity
        params.setdefault("unit", unit_label(lang, granularity))
        params.setdefault("total", total_portions(granularity))
        if "num" in params:
            params.setdefault("link", portion_url(granularity, params["num"]))
        return t(lang, key, **params)

    if bootstrapped and action == "help":
        return reply("bootstrapped") + "\n\n" + reply("help")

    if action == "help":
        return reply("help")

    if action == "lang":
        if not args:
            return reply("lang_invalid")
        raw = args[0].strip().lower()
        allowed = {
            "en",
            "fa",
            "ar",
            "english",
            "farsi",
            "persian",
            "arabic",
            "فارسی",
            "فارسي",
            "عربي",
            "عربی",
            "العربية",
            "انگلیسی",
        }
        if raw not in allowed and args[0].strip() not in allowed:
            return reply("lang_invalid")
        new_lang = normalize_lang(args[0])
        svc.set_language(group, new_lang)
        lang = new_lang
        return t(lang, "lang_set")

    if action == "startcycle":
        if not svc.is_admin(group, user_id):
            return reply("admin_only")
        result = svc.start_cycle(group)
        return reply(result.key, **result.params)

    if action == "granularity":
        if not svc.is_admin(group, user_id):
            return reply("admin_only")
        granularity = parse_granularity(args[0] if args else None)
        if granularity is None:
            return reply("granularity_invalid")
        result = svc.set_granularity(group, granularity)
        return reply(
            result.key,
            unit=unit_label(lang, granularity),
            total=total_portions(granularity),
        )

    if action == "cycle":
        if not svc.is_admin(group, user_id):
            return reply("admin_only")
        spec = parse_cycle_spec(args[0] if args else None)
        if spec is None:
            return reply("cycle_spec_invalid")
        result = svc.set_cycle_spec(group, spec)
        return reply(result.key, **result.params)

    if action == "reminders":
        if not svc.is_admin(group, user_id):
            return reply("admin_only")
        spec = parse_interval_spec(args[0] if args else None)
        if spec is None:
            return reply("reminders_invalid")
        result = svc.set_reminder_spec(group, spec)
        return reply(result.key, **result.params)

    if action == "advertise":
        if not svc.is_admin(group, user_id):
            return reply("admin_only")
        spec = parse_interval_spec(args[0] if args else None)
        if spec is None:
            return reply("advertise_invalid")
        result = svc.set_ad_spec(group, spec)
        return reply(result.key, **result.params)

    if action == "settings":
        return t(
            lang,
            "settings_overview",
            unit=unit_label(lang, group.granularity),
            total=total_portions(group.granularity),
            cycle_spec=group.cycle_spec,
            reminder_spec=group.reminder_spec,
            ad_spec=group.ad_spec,
        )

    if action == "plan":
        return _handle_plan(db, user_id=user_id, display_name=display_name, lang=lang, args=args)

    if action == "niyyah":
        if not args:
            result = svc.get_niyyah(group)
            return reply(result.key, **result.params)
        if not svc.is_admin(group, user_id):
            return reply("admin_only")
        text_arg = args[0]
        if text_arg.strip().lower() in ("clear", "none", "-", "پاک", "مسح"):
            text_arg = ""
        result = svc.set_niyyah(group, text_arg)
        return reply(result.key, **result.params)

    if action == "available":
        result = svc.available_portions(group)
        if not result.ok:
            return reply(result.key, **result.params)
        unit, _ = current_unit_and_total()
        return _format_available(lang, unit, result.data["total"], result.data["free"])

    if action == "status":
        result = svc.status(group)
        if not result.ok:
            return reply(result.key, **result.params)
        unit, _ = current_unit_and_total()
        return _format_status(lang, unit, result.data)

    if action == "mine":
        result = svc.mine(group, member)
        if not result.ok:
            return reply(result.key, **result.params)
        unit, _ = current_unit_and_total()
        return _format_mine(lang, unit, result.data["claims"])

    if action == "claim":
        num = parse_number(args[0] if args else None)
        if num is None:
            return reply("claim_invalid")
        result = svc.claim(group, member, num)
        return reply(result.key, **result.params)

    if action == "release":
        num = parse_number(args[0] if args else None)
        if num is None:
            return reply("claim_invalid")
        result = svc.release(group, member, num)
        return reply(result.key, **result.params)

    if action == "done":
        num = parse_number(args[0] if args else None)
        if num is None:
            return reply("claim_invalid")
        result = svc.mark_done(group, member, num)
        return reply(result.key, **result.params)

    if action == "admins":
        ids = svc.list_admins(group)
        lines = "\n".join(f"• {i}" for i in ids) or "—"
        return reply("admin_list", lines=lines)

    if action == "admin":
        if not svc.is_admin(group, user_id):
            return reply("admin_only")
        if len(args) < 2:
            return reply("admin_need_id")
        sub = args[0].lower()
        target = args[1].lstrip("@")
        if sub in ("add", "اضافه", "إضافة"):
            result = svc.add_admin(group, target)
            return reply(result.key, **result.params)
        if sub in ("remove", "حذف", "إزالة"):
            result = svc.remove_admin(group, target)
            return reply(result.key, **result.params)
        return reply("admin_need_id")

    return reply("unknown")
