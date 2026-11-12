
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


Category = Literal[
    "billing",
    "delivery",
    "account",
    "technical",
]

Priority = Literal["low", "medium", "high"]

TicketStatus = Literal[
    "open",
    "pending_review",
    "resolved",
]


class TicketCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    message: str = Field(
        min_length=5,
        max_length=5000,
        description="Customer support message",
        examples=["I was charged twice for my order."],
    )


class TicketDecision(BaseModel):
    category: Category
    confidence: float = Field(ge=0, le=1)
    priority: Priority
    assigned_team: str
    needs_human_review: bool
    reason: str
    model_version: str


class TicketResponse(BaseModel):
    ticket_id: str
    message: str
    category: Category
    priority: Priority
    status: TicketStatus
    created_at: datetime
    decision: TicketDecision


class TicketListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    tickets: list[TicketResponse]


class TicketReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: Category
    priority: Priority
    status: Literal["open", "resolved"]
    reviewer_note: str = Field(
        min_length=3,
        max_length=1000,
    )


class HealthResponse(BaseModel):
    status: str
    service: str
    model_loaded: bool
