"""Domain services for groups, recitation cycles, portion claims, and niyyah."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from src.config import get_settings
from src.models.entities import Cycle, Group, GroupAdmin, Member, PortionClaim
from src.quran_meta import cycle_delta, total_portions


@dataclass
class ServiceResult:
    ok: bool
    key: str
    params: dict | None = None
    data: dict | None = None

    def __post_init__(self) -> None:
        self.params = self.params or {}
        self.data = self.data or {}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class QuranGroupService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_group(self, wa_chat_id: str, title: str | None = None) -> Group:
        group = self.db.scalar(select(Group).where(Group.wa_chat_id == wa_chat_id))
        if group:
            if title and group.title != title:
                group.title = title
                self.db.commit()
            return group
        group = Group(
            wa_chat_id=wa_chat_id,
            title=title,
            language=get_settings().default_language,
        )
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        return group

    def get_or_create_member(self, group: Group, wa_user_id: str, display_name: str = "") -> Member:
        member = self.db.scalar(
            select(Member).where(Member.group_id == group.id, Member.wa_user_id == wa_user_id)
        )
        if member:
            if display_name and member.display_name != display_name:
                member.display_name = display_name
                self.db.commit()
            return member
        member = Member(group_id=group.id, wa_user_id=wa_user_id, display_name=display_name or wa_user_id)
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def is_admin(self, group: Group, wa_user_id: str) -> bool:
        if wa_user_id in get_settings().bootstrap_admins:
            return True
        row = self.db.scalar(
            select(GroupAdmin).where(GroupAdmin.group_id == group.id, GroupAdmin.wa_user_id == wa_user_id)
        )
        return row is not None

    def ensure_bootstrap_admin(self, group: Group, wa_user_id: str) -> bool:
        """If group has no admins, first interacting bootstrap user (or first user) becomes admin."""
        existing = self.db.scalars(select(GroupAdmin).where(GroupAdmin.group_id == group.id)).first()
        if existing is not None:
            return False
        settings = get_settings()
        if settings.bootstrap_admins and wa_user_id not in settings.bootstrap_admins:
            return False
        self.add_admin(group, wa_user_id)
        return True

    def add_admin(self, group: Group, wa_user_id: str) -> ServiceResult:
        existing = self.db.scalar(
            select(GroupAdmin).where(GroupAdmin.group_id == group.id, GroupAdmin.wa_user_id == wa_user_id)
        )
        if existing:
            return ServiceResult(True, "admin_added", {"id": wa_user_id})
        self.db.add(GroupAdmin(group_id=group.id, wa_user_id=wa_user_id))
        self.db.commit()
        return ServiceResult(True, "admin_added", {"id": wa_user_id})

    def remove_admin(self, group: Group, wa_user_id: str) -> ServiceResult:
        row = self.db.scalar(
            select(GroupAdmin).where(GroupAdmin.group_id == group.id, GroupAdmin.wa_user_id == wa_user_id)
        )
        if row:
            self.db.delete(row)
            self.db.commit()
        return ServiceResult(True, "admin_removed", {"id": wa_user_id})

    def list_admins(self, group: Group) -> list[str]:
        rows = self.db.scalars(select(GroupAdmin).where(GroupAdmin.group_id == group.id)).all()
        ids = [r.wa_user_id for r in rows]
        for bid in get_settings().bootstrap_admins:
            if bid not in ids:
                ids.append(bid)
        return ids

    def set_language(self, group: Group, lang: str) -> None:
        group.language = lang
        self.db.commit()

    # ---- Group settings ----------------------------------------------------

    def set_granularity(self, group: Group, granularity: str) -> ServiceResult:
        group.granularity = granularity
        self.db.commit()
        return ServiceResult(True, "granularity_set", {"granularity": granularity})

    def set_cycle_spec(self, group: Group, spec: str) -> ServiceResult:
        group.cycle_spec = spec
        self.db.commit()
        return ServiceResult(True, "cycle_spec_set", {"spec": spec})

    def set_reminder_spec(self, group: Group, spec: str) -> ServiceResult:
        group.reminder_spec = spec
        group.last_reminder_at = None
        self.db.commit()
        key = "reminders_off" if spec == "off" else "reminders_set"
        return ServiceResult(True, key, {"spec": spec})

    def set_ad_spec(self, group: Group, spec: str) -> ServiceResult:
        group.ad_spec = spec
        group.last_ad_at = None
        self.db.commit()
        key = "advertise_off" if spec == "off" else "advertise_set"
        return ServiceResult(True, key, {"spec": spec})

    # ---- Cycles ------------------------------------------------------------

    def current_cycle(self, group: Group) -> Optional[Cycle]:
        return self.db.scalar(
            select(Cycle)
            .where(Cycle.group_id == group.id, Cycle.closed_at.is_(None))
            .order_by(Cycle.cycle_number.desc())
        )

    def cycle_total(self, cycle: Cycle) -> int:
        return total_portions(cycle.granularity)

    def start_cycle(self, group: Group) -> ServiceResult:
        current = self.current_cycle(group)
        next_num = 1
        now = _utcnow()
        if current:
            current.closed_at = now
            next_num = current.cycle_number + 1
        cycle = Cycle(
            group_id=group.id,
            cycle_number=next_num,
            granularity=group.granularity,
            started_at=now,
            ends_at=now + cycle_delta(group.cycle_spec),
        )
        self.db.add(cycle)
        # New cycle resets the recurring-message clocks
        group.last_reminder_at = None
        group.last_ad_at = None
        self.db.commit()
        self.db.refresh(cycle)
        return ServiceResult(
            True,
            "cycle_started",
            {"cycle": cycle.cycle_number, "total": self.cycle_total(cycle)},
            {"cycle": cycle},
        )

    def set_niyyah(self, group: Group, text: str | None) -> ServiceResult:
        cycle = self.current_cycle(group)
        if not cycle:
            return ServiceResult(False, "claim_no_cycle")
        cleaned = (text or "").strip()
        if not cleaned:
            cycle.niyyah = None
            self.db.commit()
            return ServiceResult(True, "niyyah_cleared")
        cycle.niyyah = cleaned
        self.db.commit()
        return ServiceResult(True, "niyyah_set", {"niyyah": cleaned})

    def get_niyyah(self, group: Group) -> ServiceResult:
        cycle = self.current_cycle(group)
        if not cycle:
            return ServiceResult(False, "claim_no_cycle")
        if not cycle.niyyah:
            return ServiceResult(True, "niyyah_none")
        return ServiceResult(True, "niyyah_current", {"niyyah": cycle.niyyah})

    # ---- Portion claims ----------------------------------------------------

    def available_portions(self, group: Group) -> ServiceResult:
        cycle = self.current_cycle(group)
        if not cycle:
            return ServiceResult(False, "claim_no_cycle")
        taken = {c.portion_number for c in cycle.claims}
        total = self.cycle_total(cycle)
        free = [n for n in range(1, total + 1) if n not in taken]
        return ServiceResult(True, "available", data={"free": free, "cycle": cycle, "total": total})

    def claim(self, group: Group, member: Member, portion: int) -> ServiceResult:
        cycle = self.current_cycle(group)
        if not cycle:
            return ServiceResult(False, "claim_no_cycle")
        total = self.cycle_total(cycle)
        if portion < 1 or portion > total:
            return ServiceResult(False, "claim_invalid", {"total": total})
        existing = self.db.scalar(
            select(PortionClaim)
            .options(joinedload(PortionClaim.member))
            .where(PortionClaim.cycle_id == cycle.id, PortionClaim.portion_number == portion)
        )
        if existing:
            name = existing.member.display_name or existing.member.wa_user_id
            return ServiceResult(False, "claim_taken", {"num": portion, "name": name})
        claim = PortionClaim(cycle_id=cycle.id, member_id=member.id, portion_number=portion, status="claimed")
        self.db.add(claim)
        self.db.commit()
        return ServiceResult(True, "claim_ok", {"num": portion})

    def release(self, group: Group, member: Member, portion: int) -> ServiceResult:
        cycle = self.current_cycle(group)
        if not cycle:
            return ServiceResult(False, "claim_no_cycle")
        claim = self.db.scalar(
            select(PortionClaim).where(
                PortionClaim.cycle_id == cycle.id,
                PortionClaim.portion_number == portion,
                PortionClaim.member_id == member.id,
            )
        )
        if not claim:
            return ServiceResult(False, "release_not_yours", {"num": portion})
        self.db.delete(claim)
        self.db.commit()
        return ServiceResult(True, "release_ok", {"num": portion})

    def mark_done(self, group: Group, member: Member, portion: int) -> ServiceResult:
        cycle = self.current_cycle(group)
        if not cycle:
            return ServiceResult(False, "claim_no_cycle")
        claim = self.db.scalar(
            select(PortionClaim).where(
                PortionClaim.cycle_id == cycle.id,
                PortionClaim.portion_number == portion,
                PortionClaim.member_id == member.id,
            )
        )
        if not claim:
            return ServiceResult(False, "done_not_yours", {"num": portion})
        claim.status = "done"
        claim.done_at = _utcnow()
        self.db.commit()
        return ServiceResult(True, "done_ok", {"num": portion})

    def status(self, group: Group) -> ServiceResult:
        cycle = self.current_cycle(group)
        if not cycle:
            return ServiceResult(False, "claim_no_cycle")
        claims = self.db.scalars(
            select(PortionClaim)
            .options(joinedload(PortionClaim.member))
            .where(PortionClaim.cycle_id == cycle.id)
            .order_by(PortionClaim.portion_number)
        ).all()
        claimed = len(claims)
        done = sum(1 for c in claims if c.status == "done")
        total = self.cycle_total(cycle)
        free = total - claimed
        return ServiceResult(
            True,
            "status",
            data={
                "cycle": cycle,
                "claims": claims,
                "claimed": claimed,
                "done": done,
                "free": free,
                "total": total,
            },
        )

    def mine(self, group: Group, member: Member) -> ServiceResult:
        cycle = self.current_cycle(group)
        if not cycle:
            return ServiceResult(False, "claim_no_cycle")
        claims = self.db.scalars(
            select(PortionClaim)
            .where(PortionClaim.cycle_id == cycle.id, PortionClaim.member_id == member.id)
            .order_by(PortionClaim.portion_number)
        ).all()
        return ServiceResult(True, "mine", data={"claims": claims})
