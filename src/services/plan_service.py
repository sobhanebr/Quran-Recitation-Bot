"""Personal recitation plans managed over direct messages."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.entities import PersonalPlan
from src.quran_meta import total_portions
from src.services.group_service import ServiceResult


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def portion_range(plan: PersonalPlan) -> tuple[int, int]:
    """Inclusive (start, end) portion numbers for the current check-in."""
    total = total_portions(plan.granularity)
    start = plan.current_position
    end = min(start + plan.units_per_cycle - 1, total)
    return start, end


class PersonalPlanService:
    def __init__(self, db: Session):
        self.db = db

    def get_active_plan(self, wa_user_id: str) -> Optional[PersonalPlan]:
        return self.db.scalar(
            select(PersonalPlan).where(
                PersonalPlan.wa_user_id == wa_user_id, PersonalPlan.active.is_(True)
            )
        )

    def start_plan(
        self,
        wa_user_id: str,
        *,
        display_name: str = "",
        language: str = "en",
        granularity: str = "juz",
        units_per_cycle: int = 1,
        cycle_spec: str = "daily",
    ) -> ServiceResult:
        total = total_portions(granularity)
        units = max(1, min(units_per_cycle, total))
        existing = self.get_active_plan(wa_user_id)
        if existing:
            existing.active = False
        plan = PersonalPlan(
            wa_user_id=wa_user_id,
            display_name=display_name,
            language=language,
            granularity=granularity,
            units_per_cycle=units,
            cycle_spec=cycle_spec,
            current_position=1,
            active=True,
        )
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        start, end = portion_range(plan)
        return ServiceResult(
            True,
            "plan_started",
            {
                "count": units,
                "spec": cycle_spec,
                "start": start,
                "end": end,
                "total": total,
            },
            {"plan": plan},
        )

    def plan_status(self, wa_user_id: str) -> ServiceResult:
        plan = self.get_active_plan(wa_user_id)
        if not plan:
            return ServiceResult(False, "plan_none")
        total = total_portions(plan.granularity)
        start, end = portion_range(plan)
        done = plan.current_position - 1
        return ServiceResult(
            True,
            "plan_status",
            {
                "done": done,
                "total": total,
                "start": start,
                "end": end,
                "khatm": plan.khatm_count,
            },
            {"plan": plan},
        )

    def mark_done(self, wa_user_id: str) -> ServiceResult:
        plan = self.get_active_plan(wa_user_id)
        if not plan:
            return ServiceResult(False, "plan_none")
        total = total_portions(plan.granularity)
        start, end = portion_range(plan)
        if end >= total:
            plan.khatm_count += 1
            plan.current_position = 1
            self.db.commit()
            return ServiceResult(True, "plan_khatm", {"khatm": plan.khatm_count}, {"plan": plan})
        plan.current_position = end + 1
        self.db.commit()
        next_start, next_end = portion_range(plan)
        return ServiceResult(
            True,
            "plan_done",
            {"start": next_start, "end": next_end, "total": total},
            {"plan": plan},
        )

    def stop_plan(self, wa_user_id: str) -> ServiceResult:
        plan = self.get_active_plan(wa_user_id)
        if not plan:
            return ServiceResult(False, "plan_none")
        plan.active = False
        self.db.commit()
        return ServiceResult(True, "plan_stopped")
