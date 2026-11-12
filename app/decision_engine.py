
from app.schemas import TicketDecision

TEAM_MAPPING = {
    "billing": "payments",
    "delivery": "logistics",
    "account": "account_support",
    "technical": "technical_support",
}

HIGH_PRIORITY_KEYWORDS = (
    "charged twice",
    "duplicate charge",
    "unauthorized",
    "fraud",
    "hacked",
    "security breach",
    "data leak",
    "wrong address",
    "payment taken twice",
)

MEDIUM_PRIORITY_KEYWORDS = (
    "not working",
    "cannot login",
    "cannot log in",
    "crash",
    "error",
    "refund",
    "not arrived",
    "failed",
    "locked",
)

SENSITIVE_KEYWORDS = (
    "fraud",
    "hacked",
    "unauthorized",
    "security breach",
    "data leak",
    "charged twice",
    "duplicate charge",
)

LOW_CONFIDENCE_THRESHOLD = 0.60


def detect_priority(message: str) -> str:
    text = message.lower()

    if any(word in text for word in HIGH_PRIORITY_KEYWORDS):
        return "high"

    if any(word in text for word in MEDIUM_PRIORITY_KEYWORDS):
        return "medium"

    return "low"


def build_decision(
    message: str,
    prediction: dict,
) -> TicketDecision:

    category = prediction["category"]
    confidence = float(prediction["confidence"])

    if category not in TEAM_MAPPING:
        raise ValueError(
            f"Unsupported category: {category}"
        )

    priority = detect_priority(message)
    assigned_team = TEAM_MAPPING[category]

    text = message.lower()

    sensitive = any(
        word in text for word in SENSITIVE_KEYWORDS
    )

    uncertain = confidence < LOW_CONFIDENCE_THRESHOLD

    needs_review = sensitive or uncertain

    reasons = []

    if sensitive:
        reasons.append(
            "Sensitive customer issue detected"
        )

    if uncertain:
        reasons.append(
            "Low model confidence"
        )

    if not reasons:
        reasons.append(
            "Automatically classified and routed"
        )

    return TicketDecision(
        category=category,
        confidence=confidence,
        priority=priority,
        assigned_team=assigned_team,
        needs_human_review=needs_review,
        reason="; ".join(reasons),
        model_version=prediction["model_version"],
    )
