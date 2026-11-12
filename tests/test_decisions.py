
import pytest

from app.decision_engine import (
    detect_priority,
    build_decision,
)


def sample_prediction(
    category="billing",
    confidence=0.95,
):
    return {
        "category": category,
        "confidence": confidence,
        "model_version": "1.0.0",
    }


def test_duplicate_charge_is_high_priority():
    assert detect_priority(
        "I was charged twice for my order"
    ) == "high"


def test_refund_is_medium_priority():
    assert detect_priority(
        "My refund has not arrived"
    ) == "medium"


def test_general_question_is_low_priority():
    assert detect_priority(
        "Please send me my invoice"
    ) == "low"


def test_billing_routes_to_payments():
    decision = build_decision(
        "Please send me my invoice",
        sample_prediction(),
    )

    assert decision.category == "billing"
    assert decision.assigned_team == "payments"


def test_sensitive_ticket_requires_review():
    decision = build_decision(
        "I was charged twice",
        sample_prediction(),
    )

    assert decision.priority == "high"
    assert decision.needs_human_review is True


def test_low_confidence_requires_review():
    decision = build_decision(
        "I need help with my order",
        sample_prediction(confidence=0.40),
    )

    assert decision.needs_human_review is True
    assert "Low model confidence" in decision.reason


def test_high_confidence_normal_ticket():
    decision = build_decision(
        "Please send me my invoice",
        sample_prediction(confidence=0.95),
    )

    assert decision.needs_human_review is False


def test_unknown_category_rejected():
    with pytest.raises(ValueError):
        build_decision(
            "Hello",
            sample_prediction(category="unknown"),
        )
