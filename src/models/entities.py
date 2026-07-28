"""Domain models for shared recitation cycles and personal plans."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.db import Base
from src.quran_meta import (
    DEFAULT_AD_SPEC,
    DEFAULT_CYCLE_SPEC,
    DEFAULT_GRANULARITY,
    DEFAULT_REMINDER_SPEC,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    wa_chat_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(String(8), default="en")
    # Recitation settings
    granularity: Mapped[str] = mapped_column(String(16), default=DEFAULT_GRANULARITY)
    cycle_spec: Mapped[str] = mapped_column(String(16), default=DEFAULT_CYCLE_SPEC)
    reminder_spec: Mapped[str] = mapped_column(String(16), default=DEFAULT_REMINDER_SPEC)
    ad_spec: Mapped[str] = mapped_column(String(16), default=DEFAULT_AD_SPEC)
    last_reminder_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_ad_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    members: Mapped[list[Member]] = relationship(back_populates="group", cascade="all, delete-orphan")
    cycles: Mapped[list[Cycle]] = relationship(back_populates="group", cascade="all, delete-orphan")
    admins: Mapped[list[GroupAdmin]] = relationship(back_populates="group", cascade="all, delete-orphan")


class Member(Base):
    __tablename__ = "members"
    __table_args__ = (UniqueConstraint("group_id", "wa_user_id", name="uq_member_group_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    wa_user_id: Mapped[str] = mapped_column(String(64), index=True)
    display_name: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    group: Mapped[Group] = relationship(back_populates="members")
    claims: Mapped[list[PortionClaim]] = relationship(back_populates="member")


class GroupAdmin(Base):
    __tablename__ = "group_admins"
    __table_args__ = (UniqueConstraint("group_id", "wa_user_id", name="uq_admin_group_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    wa_user_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    group: Mapped[Group] = relationship(back_populates="admins")


class Cycle(Base):
    """A recitation cycle (formerly a fixed week)."""

    __tablename__ = "cycles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    cycle_number: Mapped[int] = mapped_column(Integer)
    granularity: Mapped[str] = mapped_column(String(16), default=DEFAULT_GRANULARITY)
    niyyah: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    group: Mapped[Group] = relationship(back_populates="cycles")
    claims: Mapped[list[PortionClaim]] = relationship(back_populates="cycle", cascade="all, delete-orphan")


class PortionClaim(Base):
    __tablename__ = "portion_claims"
    __table_args__ = (UniqueConstraint("cycle_id", "portion_number", name="uq_cycle_portion"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("cycles.id"), index=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), index=True)
    portion_number: Mapped[int] = mapped_column(Integer)  # 1..total for the cycle granularity
    status: Mapped[str] = mapped_column(String(16), default="claimed")  # claimed | done
    claimed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    done_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    cycle: Mapped[Cycle] = relationship(back_populates="claims")
    member: Mapped[Member] = relationship(back_populates="claims")


class PersonalPlan(Base):
    """An individual recitation plan managed over direct messages."""

    __tablename__ = "personal_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    wa_user_id: Mapped[str] = mapped_column(String(64), index=True)
    display_name: Mapped[str] = mapped_column(String(255), default="")
    language: Mapped[str] = mapped_column(String(8), default="en")
    granularity: Mapped[str] = mapped_column(String(16), default=DEFAULT_GRANULARITY)
    units_per_cycle: Mapped[int] = mapped_column(Integer, default=1)
    cycle_spec: Mapped[str] = mapped_column(String(16), default="daily")
    current_position: Mapped[int] = mapped_column(Integer, default=1)  # next portion to read (1-based)
    khatm_count: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_reminder_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
