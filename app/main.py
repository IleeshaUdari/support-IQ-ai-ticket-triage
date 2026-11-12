
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.concurrency import run_in_threadpool

from app.classifier import load_model, predict_ticket
from app.database import (
    initialize_database,
    create_ticket,
    get_ticket,
    list_tickets,
    update_ticket_review,
    get_ticket_reviews,
)
from app.decision_engine import (
    build_decision,
    TEAM_MAPPING,
    HIGH_PRIORITY_KEYWORDS,
    MEDIUM_PRIORITY_KEYWORDS,
    SENSITIVE_KEYWORDS,
    LOW_CONFIDENCE_THRESHOLD,
)
from app.schemas import (
    TicketCreate,
    TicketResponse,
    TicketDecision,
    TicketListResponse,
    TicketReview,
    HealthResponse,
    TicketStatus,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    load_model()
    yield


app = FastAPI(
    title="SupportIQ AI API",
    description=(
        "AI-powered customer support classification, "
        "prioritization and routing."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


def format_ticket(row):
    if row is None:
        return None

    message = row["message"]
    confidence = float(row["confidence"])

    # Reconstruct the original decision from stored data.
    # A later human correction does not change this record.
    predicted_category = row["predicted_category"]

    sensitive = any(
        word in message.lower()
        for word in SENSITIVE_KEYWORDS
    )

    uncertain = confidence < LOW_CONFIDENCE_THRESHOLD

    reasons = []

    if sensitive:
        reasons.append("Sensitive customer issue detected")

    if uncertain:
        reasons.append("Low model confidence")

    if not reasons:
        reasons.append("Automatically classified and routed")

    original_priority = "low"
    text = message.lower()

    if any(word in text for word in HIGH_PRIORITY_KEYWORDS):
        original_priority = "high"
    elif any(word in text for word in MEDIUM_PRIORITY_KEYWORDS):
        original_priority = "medium"

    decision = TicketDecision(
        category=predicted_category,
        confidence=confidence,
        priority=original_priority,
        assigned_team=row["assigned_team"],
        needs_human_review=bool(row["needs_human_review"]),
        reason="; ".join(reasons),
        model_version=row["model_version"],
    )

    return TicketResponse(
        ticket_id=row["ticket_id"],
        message=message,
        category=row["category"],
        priority=row["priority"],
        status=row["status"],
        created_at=row["created_at"],
        decision=decision,
    )


def process_ticket(message: str):
    prediction = predict_ticket(message)
    decision = build_decision(message, prediction)

    ticket_id = f"TKT-{uuid4().hex[:12].upper()}"

    row = create_ticket(
        ticket_id=ticket_id,
        message=message,
        decision=decision,
    )

    return format_ticket(row)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
)
def health_check():
    try:
        load_model()
        loaded = True
    except Exception:
        loaded = False

    return HealthResponse(
        status="healthy" if loaded else "degraded",
        service="supportiq-api",
        model_loaded=loaded,
    )


@app.post(
    "/api/v1/tickets",
    response_model=TicketResponse,
    status_code=201,
    tags=["Tickets"],
)
async def submit_ticket(payload: TicketCreate):
    # ML inference and SQLite are synchronous operations.
    # Run them in a worker thread.
    return await run_in_threadpool(
        process_ticket,
        payload.message,
    )


@app.get(
    "/api/v1/tickets",
    response_model=TicketListResponse,
    tags=["Tickets"],
)
def get_tickets(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: TicketStatus | None = None,
):
    total, rows = list_tickets(
        limit=limit,
        offset=offset,
        status=status,
    )

    return TicketListResponse(
        total=total,
        limit=limit,
        offset=offset,
        tickets=[format_ticket(row) for row in rows],
    )


@app.get(
    "/api/v1/tickets/{ticket_id}",
    response_model=TicketResponse,
    tags=["Tickets"],
)
def get_ticket_by_id(ticket_id: str):
    row = get_ticket(ticket_id)

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    return format_ticket(row)


@app.patch(
    "/api/v1/tickets/{ticket_id}/review",
    response_model=TicketResponse,
    tags=["Human Review"],
)


@app.patch(
    "/api/v1/tickets/{ticket_id}/review",
    response_model=TicketResponse,
    tags=["Human Review"],
)


@app.patch(
    "/api/v1/tickets/{ticket_id}/review",
    response_model=TicketResponse,
    tags=["Human Review"],
)
def review_ticket(ticket_id: str, payload: TicketReview):
    row = update_ticket_review(
        ticket_id=ticket_id,
        category=payload.category,
        priority=payload.priority,
        status=payload.status,
        reviewer_note=payload.reviewer_note,
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    return format_ticket(row)



@app.get(
    "/api/v1/tickets/{ticket_id}/reviews",
    tags=["Human Review"],
)
def list_ticket_reviews(ticket_id: str):
    if get_ticket(ticket_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    return {
        "ticket_id": ticket_id,
        "reviews": get_ticket_reviews(ticket_id),
    }
