
import pytest
from fastapi.testclient import TestClient

import app.database as database
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Each test receives a fresh SQLite database.
    test_db = tmp_path / "test_supportiq.db"

    monkeypatch.setattr(
        database,
        "DB_PATH",
        test_db,
    )

    with TestClient(app) as test_client:
        yield test_client


def create_sample_ticket(client):
    response = client.post(
        "/api/v1/tickets",
        json={
            "message": "I was charged twice for my order."
        },
    )

    assert response.status_code == 201

    return response.json()


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["model_loaded"] is True


def test_create_ticket(client):
    ticket = create_sample_ticket(client)

    assert ticket["ticket_id"].startswith("TKT-")
    assert ticket["priority"] == "high"
    assert ticket["status"] == "pending_review"
    assert ticket["decision"]["needs_human_review"] is True


def test_ticket_persisted(client):
    ticket = create_sample_ticket(client)

    response = client.get(
        f"/api/v1/tickets/{ticket['ticket_id']}"
    )

    assert response.status_code == 200
    assert response.json()["ticket_id"] == ticket["ticket_id"]


def test_list_tickets(client):
    create_sample_ticket(client)

    response = client.get("/api/v1/tickets")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["tickets"]) == 1


def test_filter_pending_review(client):
    create_sample_ticket(client)

    response = client.get(
        "/api/v1/tickets?status=pending_review"
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_empty_message_rejected(client):
    response = client.post(
        "/api/v1/tickets",
        json={"message": ""},
    )

    assert response.status_code == 422


def test_unknown_ticket_returns_404(client):
    response = client.get(
        "/api/v1/tickets/TKT-UNKNOWN"
    )

    assert response.status_code == 404


def test_human_review(client):
    ticket = create_sample_ticket(client)

    response = client.patch(
        f"/api/v1/tickets/{ticket['ticket_id']}/review",
        json={
            "category": "billing",
            "priority": "high",
            "status": "resolved",
            "reviewer_note": "Refund verified by reviewer.",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "resolved"


def test_review_history(client):
    ticket = create_sample_ticket(client)

    client.patch(
        f"/api/v1/tickets/{ticket['ticket_id']}/review",
        json={
            "category": "billing",
            "priority": "high",
            "status": "resolved",
            "reviewer_note": "Customer refund confirmed.",
        },
    )

    response = client.get(
        f"/api/v1/tickets/{ticket['ticket_id']}/reviews"
    )

    assert response.status_code == 200

    reviews = response.json()["reviews"]

    assert len(reviews) == 1
    assert reviews[0]["reviewer_note"] == (
        "Customer refund confirmed."
    )


def test_invalid_category_rejected(client):
    ticket = create_sample_ticket(client)

    response = client.patch(
        f"/api/v1/tickets/{ticket['ticket_id']}/review",
        json={
            "category": "unknown",
            "priority": "high",
            "status": "resolved",
            "reviewer_note": "Invalid category test.",
        },
    )

    assert response.status_code == 422


def test_pagination_validation(client):
    response = client.get(
        "/api/v1/tickets?limit=1000"
    )

    assert response.status_code == 422
