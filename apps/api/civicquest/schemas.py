from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Point(Input):
    lat: float = Field(ge=-90, le=90, allow_inf_nan=False)
    lng: float = Field(ge=-180, le=180, allow_inf_nan=False)
    accuracy_m: float | None = Field(default=None, ge=0, le=100000, allow_inf_nan=False)


PORTRAITS = [
    {"id": "explorer", "name": "Explorer"},
    {"id": "observer", "name": "Observer"},
    {"id": "neighbour", "name": "Neighbour"},
    {"id": "maker", "name": "Maker"},
    {"id": "gardener", "name": "Gardener"},
    {"id": "navigator", "name": "Navigator"},
]


class Portrait(Input):
    portrait_id: Literal["explorer", "observer", "neighbour", "maker", "gardener", "navigator"] | None


class Draft(Point):
    report_type: Literal["place", "civic_catch"] = "place"
    category: str = Field(min_length=1, max_length=60)
    title: str = Field(default="", max_length=160)
    description: str = Field(default="", max_length=2000)
    address: str = Field(default="Mumbai", max_length=200)
    severity: Literal["low", "medium", "high"] = "medium"


class Upload(Input):
    content_type: Literal["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"]
    size: int = Field(gt=0, le=20 * 1024 * 1024)
    role: Literal["evidence", "before", "after", "team"] = "evidence"


class CatchUpload(Input):
    content_type: Literal["image/jpeg", "video/webm", "video/mp4"]
    size: int = Field(gt=0, le=50 * 1024 * 1024)
    role: Literal["evidence"] = "evidence"


class CatchFinalize(Input):
    category: str = Field(default="littering", min_length=1, max_length=60)
    description: str = Field(min_length=2, max_length=1000)
    address: str = Field(min_length=2, max_length=200)


class VerificationInput(Input):
    result: Literal["confirmed", "disputed", "not_found"]


class Reason(Input):
    reason: str = Field(min_length=5, max_length=2000)


class ReportMessageInput(Input):
    body: str = Field(min_length=2, max_length=1200)
    kind: Literal["comment", "community_update"] = "comment"


class MessageModeration(Reason):
    decision: Literal["keep", "restrict", "remove"]


class EscalationDecision(Reason):
    approved: bool


class ComplaintInput(Input):
    source_name: str = Field(min_length=2, max_length=120)
    source_url: str | None = Field(default=None, max_length=2048)
    official_id: str | None = Field(default=None, max_length=120)
    receipt_key: str | None = Field(default=None, max_length=500)


class ComplaintStatusInput(Input):
    status: str = Field(min_length=2, max_length=120)
    occurred_at: datetime
    source_note: str = Field(default="", max_length=2000)


class CommunityGroupInput(Input):
    name: str = Field(min_length=2, max_length=160)
    description: str = Field(min_length=5, max_length=3000)
    area_id: str | None = None
    coverage_text: str = Field(min_length=2, max_length=300)
    contact_url: str = Field(min_length=8, max_length=2048)
    source_url: str = Field(min_length=8, max_length=2048)
    source_name: str = Field(min_length=2, max_length=160)
    verified_at: datetime
    reviewed: bool = False
    status: Literal["active", "inactive"] = "active"
    statistics: dict[str, str | int | float] = Field(default_factory=dict)


class OfficerInput(Input):
    name: str = Field(min_length=2, max_length=160)
    title: str = Field(min_length=2, max_length=160)
    department: str = Field(min_length=2, max_length=160)
    area_id: str | None = None
    category_family: str | None = Field(default=None, max_length=80)
    reason: str = Field(min_length=5, max_length=1000)
    source_url: str = Field(min_length=8, max_length=2048)
    verified_at: datetime
    effective_to: datetime | None = None
    phone: str | None = Field(default=None, max_length=40)
    whatsapp: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=320)
    official_url: str | None = Field(default=None, max_length=2048)
    reviewed: bool = False


class AuthorityInput(Input):
    name: str = Field(min_length=2, max_length=160)
    department: str = Field(min_length=2, max_length=160)
    area_id: str
    category_family: str = Field(min_length=2, max_length=80)
    source_url: str = Field(min_length=8, max_length=2048)
    effective_from: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    effective_to: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    reviewed: bool = False


class Review(Reason):
    decision: Literal[
        "publish", "verify", "restrict", "remove", "reject", "restore", "acknowledge", "in_progress"
    ]


class AppealInput(Reason):
    target_type: Literal["report", "action"]
    target_id: str


class Decision(Reason):
    approved: bool


class ResolutionInput(Input):
    description: str = Field(min_length=5, max_length=2000)


class ActionInput(Point):
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=5, max_length=4000)
    organizer: str = Field(min_length=2, max_length=120)
    location_name: str = Field(min_length=2, max_length=160)
    starts_at: datetime
    ends_at: datetime
    capacity: int = Field(default=50, gt=0, le=10000)
    status: Literal["draft", "published", "cancelled", "completed"] = "draft"

    @model_validator(mode="after")
    def valid_time(self):
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None or self.ends_at <= self.starts_at:
            raise ValueError("Event needs timezone-aware start/end and positive duration")
        return self


class Checkin(Point):
    challenge: str


class Handle(Input):
    handle: str = Field(pattern=r"^[a-z][a-z0-9_]{2,23}$")
    display_name: str = Field(min_length=2, max_length=60)


class Share(Input):
    kind: Literal[
        "achievement", "civic_card", "monthly", "cleanup", "ward", "resolved_fix", "before_after"
    ]
    action_id: str | None = None
    report_id: str | None = None
    area_id: str | None = None


class Redaction(Input):
    boxes: list[tuple[float, float, float, float]] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def bounds(self):
 