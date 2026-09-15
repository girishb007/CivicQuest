"""PostgreSQL source records. Reward and audit histories are append-only."""

import uuid

from geoalchemy2 import Geography, Geometry
from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base, now


def uid():
    return str(uuid.uuid4())


class Record:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now, index=True)


class User(Record, Base):
    __tablename__ = "users"
    identity_type: Mapped[str] = mapped_column(default="guest")
    role: Mapped[str] = mapped_column(default="citizen")
    status: Mapped[str] = mapped_column(default="active")
    handle: Mapped[str | None] = mapped_column(String(32), unique=True)
    display_name: Mapped[str] = mapped_column(default="Mumbai explorer")
    portrait_id: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(320))
    merged_into: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    home_area_id: Mapped[str | None] = mapped_column(String(36))
    notify_report_updates: Mapped[bool] = mapped_column(default=True)
    notify_action_reminders: Mapped[bool] = mapped_column(default=True)
    notify_push: Mapped[bool] = mapped_column(default=False)
    __table_args__ = (
        CheckConstraint("identity_type in ('guest','registered')"),
        CheckConstraint("role in ('citizen','moderator','admin')"),
    )


class Identity(Record, Base):
    __tablename__ = "auth_identities"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    provider: Mapped[str]
    subject: Mapped[str]
    __table_args__ = (UniqueConstraint("provider", "subject"),)


class Session(Record, Base):
    __tablename__ = "sessions"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(unique=True)
    csrf_hash: Mapped[str]
    expires_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(default=False)


class OAuthState(Record, Base):
    __tablename__ = "oauth_states"
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"))
    state_hash: Mapped[str] = mapped_column(unique=True)
    nonce: Mapped[str]
    verifier: Mapped[str]
    expires_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    consumed: Mapped[bool] = mapped_column(default=False)


class Dataset(Record, Base):
    __tablename__ = "datasets"
    name: Mapped[str]
    version: Mapped[str]
    source_url: Mapped[str]
    license: Mapped[str]
    reviewed: Mapped[bool] = mapped_column(default=False)
    synthetic: Mapped[bool] = mapped_column(default=False)
    checksum: Mapped[str]
    __table_args__ = (UniqueConstraint("name", "version"),)


class Area(Record, Base):
    __tablename__ = "administrative_areas"
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id"))
    code: Mapped[str]
    name: Mapped[str]
    area_type: Mapped[str] = mapped_column(default="ward")
    boundary: Mapped[object] = mapped_column(Geometry("MULTIPOLYGON", srid=4326))
    active: Mapped[bool] = mapped_column(default=True)
    effective_from: Mapped[str | None]
    effective_to: Mapped[str | None]
    __table_args__ = (UniqueConstraint("dataset_id", "code", "area_type"),)


class PostalPlace(Record, Base):
    __tablename__ = "postal_places"
    pincode: Mapped[str] = mapped_column(String(6), index=True)
    office_name: Mapped[str]
    district: Mapped[str]
    location: Mapped[object] = mapped_column(Geography("POINT", srid=4326))
    source_url: Mapped[str]
    source_version: Mapped[str]
    fetched_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    active: Mapped[bool] = mapped_column(default=True)
    __table_args__ = (UniqueConstraint("pincode", "office_name"),)


class Authority(Record, Base):
    __tablename__ = "authorities"
    name: Mapped[str]
    department: Mapped[str]
    area_id: Mapped[str] = mapped_column(ForeignKey("administrative_areas.id"))
    category_family: Mapped[str]
    source_url: Mapped[str]
    effective_from: Mapped[str]
    effective_to: Mapped[str | None]
    reviewed: Mapped[bool] = mapped_column(default=False)


class Representative(Record, Base):
    __tablename__ = "representatives"
    name: Mapped[str]
    role: Mapped[str]
    area_id: Mapped[str] = mapped_column(ForeignKey("administrative_areas.id"))
    source_url: Mapped[str]
    source_name: Mapped[str | None]
    source_id: Mapped[str | None] = mapped_column(String(120), index=True)
    party: Mapped[str | None]
    photo_url: Mapped[str | None]
    fetched_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    effective_from: Mapped[str]
    effective_to: Mapped[str | None]
    reviewed: Mapped[bool] = mapped_column(default=False)


class Officer(Record, Base):
    __tablename__ = "officers"
    name: Mapped[str]
    title: Mapped[str]
    department: Mapped[str]
    area_id: Mapped[str | None] = mapped_column(ForeignKey("administrative_areas.id"), index=True)
    category_family: Mapped[str | None]
    reason: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str]
    verified_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    phone: Mapped[str | None]
    whatsapp: Mapped[str | None]
    email: Mapped[str | None]
    official_url: Mapped[str | None]
    reviewed: Mapped[bool] = mapped_column(default=False)


class CommunityGroup(Record, Base):
    __tablename__ = "community_groups"
    name: Mapped[str]
    description: Mapped[str] = mapped_column(Text)
    area_id: Mapped[str | None] = mapped_column(ForeignKey("administrative_areas.id"), index=True)
    coverage_text: Mapped[str]
    contact_url: Mapped[str]
    source_url: Mapped[str]
    source_name: Mapped[str]
    verified_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    reviewed: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(default="active")
    statistics: Mapped[dict] = mapped_column(JSON, default=dict)
    __table_args__ = (CheckConstraint("status in ('active','inactive')"),)


class Category(Base):
    __tablename__ = "categories"
    code: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    report_type: Mapped[str]
    family: Mapped[str]
    active: Mapped[bool] = mapped_column(default=True)


class Report(Record, Base):
    __tablename__ = "reports"
    reporter_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    public_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        server_default=text("'CQ-MUM-' || lpad(nextval('report_public_code_seq')::text, 6, '0')"),
    )
    report_type: Mapped[str]
    category: Mapped[str] = mapped_column(ForeignKey("categories.code"))
    title: Mapped[str] = mapped_column(String(160), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[object] = mapped_column(Geography("POINT", srid=4326))
    accuracy_m: Mapped[float | None]
    address: Mapped[str] = mapped_column(default="Mumbai")
    area_id: Mapped[str | None] = mapped_column(ForeignKey("administrative_areas.id"), index=True)
    authority_id: Mapped[str | None] = mapped_column(ForeignKey("authorities.id"))
    status: Mapped[str] = mapped_column(default="draft", index=True)
    visibility: Mapped[str] = mapped_column(default="private", index=True)
    verification: Mapped[str] = mapped_column(default="unverified")
    severity: Mapped[int] = mapped_column(default=2)
    duplicate_of: Mapped[str | None] = mapped_column(ForeignKey("reports.id"))
    demo: Mapped[bool] = mapped_column(default=False)
    finalized_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("report_type in ('place','civic_catch')"),
        CheckConstraint("visibility in ('private','pending','public','restricted','removed')"),
        CheckConstraint(
            "status in ('draft','processing','open','acknowledged','in_progress','resolved','rejected')"
        ),
        CheckConstraint("severity between 1 and 5"),
        Index("report_public_feed", "visibility", "status", "created_at"),
        Index(
            "report_public_recent",
            "created_at",
            "id",
            postgresql_where=text(
                "visibility = 'public' AND duplicate_of IS NULL AND status NOT IN ('draft','processing','rejected')"
            ),
        ),
    )


class ReportMilestone(Record, Base):
    __tablename__ = "report_milestones"
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), index=True)
    kind: Mapped[str]
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    __table_args__ = (UniqueConstraint("report_id", "kind", name="uq_report_milestone_kind"),)


class CatchCaptureSession(Record, Base):
    __tablename__ = "catch_capture_sessions"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    location: Mapped[object] = mapped_column(Geography("POINT", srid=4326))
    accuracy_m: Mapped[float]
    expires_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    report_id: Mapped[str | None] = mapped_column(ForeignKey("reports.id"), unique=True)


class Media(Record, Base):
    __tablename__ = "media"
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    report_id: Mapped[str | None] = mapped_column(ForeignKey("reports.id"), index=True)
    action_id: Mapped[str | None] = mapped_column(ForeignKey("civic_actions.id"))
    resolution_id: Mapped[str | None] = mapped_column(ForeignKey("resolutions.id"))
    capture_session_id: Mapped[str | None] = mapped_column(ForeignKey("catch_capture_sessions.id"), index=True)
    role: Mapped[str] = mapped_column(default="evidence")
    original_key: Mapped[str]
    public_key: Mapped[str | None]
    content_type: Mapped[str]
    size: Mapped[int]
    sha256: Mapped[str | None]
    phash: Mapped[str | None]
    state: Mapped[str] = mapped_column(default="awaiting_upload")
    upload_token_hash: Mapped[str]
    upload_expires: Mapped[object] = mapped_column(DateTime(timezone=True))
    flags: Mapped[dict] = mapped_column(JSON, default=dict)
    redacted: Mapped[bool] = mapped_column(default=False)
    purged_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))


class Vote(Base):
    __tablename__ = "report_votes"
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now)


class SeenConfirmation(Base):
    __tablename__ = "seen_confirmations"
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now)


class ReportFollow(Base):
    __tablename__ = "report_follows"
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now)


class ReportMessage(Record, Base):
    __tablename__ = "report_messages"
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str] = mapped_column(default="comment")
    body: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(default="published")
    moderated_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    moderated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("kind in ('comment','community_update')"),
        CheckConstraint("state in ('published','restricted','removed')"),
    )


class EscalationCase(Record, Base):
    __tablename__ = "escalation_cases"
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), unique=True, index=True)
    threshold: Mapped[int] = mapped_column(default=10)
    state: Mapped[str] = mapped_column(default="review")
    reviewed_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    decision_reason: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        CheckConstraint("threshold > 0"),
        CheckConstraint("state in ('review','approved','declined','handed_off','closed')"),
    )


class Complaint(Record, Base):
    __tablename__ = "complaints"
    escalation_id: Mapped[str] = mapped_column(ForeignKey("escalation_cases.id"), unique=True)
    official_id: Mapped[str | None] = mapped_column(String(120), unique=True)
    source_name: Mapped[str]
    source_url: Mapped[str | None] = mapped_column(Text)
    receipt_key: Mapped[str | None]
    handed_off_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    last_checked_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))


class ComplaintStatusEvent(Record, Base):
    __tablename__ = "complaint_status_events"
    complaint_id: Mapped[str] = mapped_column(ForeignKey("complaints.id"), index=True)
    status: Mapped[str]
    occurred_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    source_note: Mapped[str] = mapped_column(Text, default="")
    recorded_by: Mapped[str] = mapped_column(ForeignKey("users.id"))


class Verification(Record, Base):
    __tablename__ = "verifications"
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    result: Mapped[str]
    accepted: Mapped[bool] = mapped_column(default=False)
    __table_args__ = (
        UniqueConstraint("report_id", "user_id"),
        CheckConstraint("result in ('confirmed','disputed','not_found')"),
    )


class Resolution(Record, Base):
    __tablename__ = "resolutions"
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    description: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(default="draft")
    reviewed_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))


class ResolutionVerification(Record, Base):
    __tablename__ = "resolution_verifications"
    resolution_id: Mapped[str] = mapped_column(ForeignKey("resolutions.id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    result: Mapped[str]
    accepted: Mapped[bool] = mapped_column(default=False)
    __table_args__ = (UniqueConstraint("resolution_id", "user_id"),)


class Audit(Record, Base):
    __tablename__ = "audit_events"
    actor_id: Mapped[str | None] = mapped_column(String(36))
    target_type: Mapped[str]
    target_id: Mapped[str] = mapped_column(index=True)
    action: Mapped[str]
    before: Mapped[dict] = mapped_column(JSON, default=dict)
    after: Mapped[dict] = mapped_column(JSON, default=dict)
    reason: Mapped[str] = mapped_column(Text, default="")
    public: Mapped[bool] = mapped_column(default=False)


class ModerationCase(Record, Base):
    __tablename__ = "moderation_cases"
    report_id: Mapped[str | None] = mapped_column(ForeignKey("reports.id"), index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str]
    priority: Mapped[int] = mapped_column(default=2)
    state: Mapped[str] = mapped_column(default="open")
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    decision: Mapped[str | None]
    closed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))


class Appeal(Record, Base):
    __tablename__ = "appeals"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    target_type: Mapped[str]
    target_id: Mapped[str]
    reason: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(default="open")
    decision: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))


class XPEvent(Record, Base):
    __tablename__ = "xp_events"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    points: Mapped[int]
    event_type: Mapped[str]
    source_type: Mapped[str]
    source_id: Mapped[str]
    idempotency_key: Mapped[str] = mapped_column(unique=True)
    reversal_of: Mapped[str | None] = mapped_column(ForeignKey("xp_events.id"), unique=True)
    rule_version: Mapped[str] = mapped_column(default="v1")
    local_date: Mapped[str] = mapped_column(index=True)
    capped: Mapped[bool] = mapped_column(default=True)


class Badge(Base):
    __tablename__ = "user_badges"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    code: Mapped[str] = mapped_column(primary_key=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now)
    rule_version: Mapped[str] = mapped_column(default="v1-mobile")


class Dex(Base):
    __tablename__ = "user_civicdex"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    category: Mapped[str] = mapped_column(ForeignKey("categories.code"), primary_key=True)
    verified_count: Mapped[int] = mapped_column(default=1)


class QuestProgress(Base):
    __tablename__ = "quest_progress"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    code: Mapped[str] = mapped_column(primary_key=True)
    period: Mapped[str] = mapped_column(primary_key=True)
    progress: Mapped[int] = mapped_column(default=0)
    completed: Mapped[bool] = mapped_column(default=False)


class LeaderboardSnapshot(Record, Base):
    __tablename__ = "leaderboard_snapshots"
    scope: Mapped[str]
    period: Mapped[str]
    entries: Mapped[list] = mapped_column(JSON)


class Hotspot(Record, Base):
    __tablename__ = "hotspots"
    anchor_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), unique=True)
    name: Mapped[str]
    family: Mapped[str]
    area_id: Mapped[str | None] = mapped_column(ForeignKey("administrative_areas.id"))
    location: Mapped[object] = mapped_column(Geography("POINT", srid=4326))
    score: Mapped[float] = mapped_column(default=0)
    score_version: Mapped[str] = mapped_column(default="v1")
    active: Mapped[bool] = mapped_column(default=True)


class HotspotReport(Base):
    __tablename__ = "hotspot_reports"
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), primary_key=True)
    hotspot_id: Mapped[str] = mapped_column(ForeignKey("hotspots.id"), index=True)


class CivicAction(Record, Base):
    __tablename__ = "civic_actions"
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str]
    description: Mapped[str] = mapped_column(Text)
    organizer: Mapped[str]
    location_name: Mapped[str]
    location: Mapped[object] = mapped_column(Geography("POINT", srid=4326))
    starts_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    capacity: Mapped[int] = mapped_column(default=50)
    status: Mapped[str] = mapped_column(default="draft")
    demo: Mapped[bool] = mapped_column(default=False)
    __table_args__ = (CheckConstraint("capacity > 0"), CheckConstraint("ends_at > starts_at"))


class Participation(Base):
    __tablename__ = "action_participants"
    action_id: Mapped[str] = mapped_column(ForeignKey("civic_actions.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    joined_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now)
    checked_in_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    state: Mapped[str] = mapped_column(default="joined")
    reviewed_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    review_reason: Mapped[str | None]


class Challenge(Record, Base):
    __tablename__ = "checkin_challenges"
    action_id: Mapped[str] = mapped_column(ForeignKey("civic_actions.id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    token_hash: Mapped[str] = mapped_column(unique=True)
    expires_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(default=False)


class WardGoal(Record, Base):
    __tablename__ = "ward_goals"
    area_id: Mapped[str] = mapped_column(ForeignKey("administrative_areas.id"), index=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(160))
    target: Mapped[int]
    starts_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(default="draft")
    __table_args__ = (CheckConstraint("target > 0"), CheckConstraint("ends_at > starts_at"),
                      CheckConstraint("status in ('draft','published','cancelled')"))


class Outbox(Record, Base):
    __tablename__ = "outbox"
    kind: Mapped[str]
    payload: Mapped[dict] = mapped_column(JSON)
    dedupe_key: Mapped[str] = mapped_column(unique=True)
    attempts: Mapped[int] = mapped_column(default=0)
    available_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now, index=True)
    dispatched_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    state: Mapped[str] = mapped_column(default="pending", index=True)
    error: Mapped[str | None]


class Receipt(Base):
    __tablename__ = "job_receipts"
    event_id: Mapped[str] = mapped_column(ForeignKey("outbox.id"), primary_key=True)
    completed_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now)


class Notification(Record, Base):
    __tablename__ = "notifications"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str]
    body: Mapped[str]
    href: Mapped[str]
    dedupe_key: Mapped[str] = mapped_column(unique=True)
    read_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))


class PushSubscription(Record, Base):
    __tablename__ = "push_subscriptions"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    endpoint: Mapped[str] = mapped_column(Text, unique=True)
    keys: Mapped[dict] = mapped_column(JSON)


class ShareCard(Record, Base):
    __tablename__ = "share_cards"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str]
    action_id: Mapped[str | None] = mapped_column(ForeignKey("civic_actions.id"))
    report_id: Mapped[str | None] = mapped_column(ForeignKey("reports.id"), index=True)
    area_id: Mapped[str | None] = mapped_column(ForeignKey("administrative_areas.id"), index=True)
    object_key: Mapped[str | None]
    state: Mapped[str] = mapped_column(default="pending")


class Mutation(Record, Base):
    __tablename__ = "idempotent_mutations"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    operation: Mapped[str]
    key: Mapped[str]
    request_hash: Mapped[str]
    result: Mapped[dict] = mapped_column(JSON)
    __table_args__ = (UniqueConstraint("user_id", "operation", "key"),)
