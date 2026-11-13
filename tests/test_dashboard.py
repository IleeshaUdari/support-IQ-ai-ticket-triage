
from unittest.mock import Mock

import pytest
import requests

from dashboard.api_client import (
    APIError,
    SupportIQClient,
)


@pytest.fixture
def session():
    return Mock()


@pytest.fixture
def client(session):
    return SupportIQClient(
        base_url="http://localhost:8000",
        session=session,
    )


def mock_response(data, status=200):
    response = Mock()
    response.status_code = status
    response.json.return_value = data
    response.raise_for_status.return_value = None
    return response


def test_health(client, session):
    session.request.return_value = mock_response({
        "status": "healthy",
        "model_loaded": True,
    })

    result = client.health()

    assert result["status"] == "healthy"

    session.request.assert_called_once_with(
        "GET",
        "http://localhost:8000/health",
        timeout=15,
    )


def test_create_ticket(client, session):
    session.request.return_value = mock_response({
        "ticket_id": "TKT-123",
        "category": "billing",
    })

    result = client.create_ticket(
        "I was charged twice"
    )

    assert result["category"] == "billing"

    assert session.request.call_args.kwargs["json"] == {
        "message": "I was charged twice"
    }


def test_get_ticket(client, session):
    session.request.return_value = mock_response({
        "ticket_id": "TKT-123"
    })

    result = client.get_ticket("TKT-123")

    assert result["ticket_id"] == "TKT-123"


def test_get_all_tickets(client, session):
    session.request.side_effect = [
        mock_response({
            "total": 2,
            "tickets": [
                {"ticket_id": "TKT-1"},
                {"ticket_id": "TKT-2"},
            ],
        }),
    ]

    tickets = client.get_all_tickets()

    assert len(tickets) == 2


def test_review_ticket(client, session):
    session.request.return_value = mock_response({
        "status": "resolved"
    })

    result = client.review_ticket(
        ticket_id="TKT-123",
        category="billing",
        priority="high",
        status="resolved",
        reviewer_note="Refund confirmed",
    )

    assert result["status"] == "resolved"


def test_review_history(client, session):
    session.request.return_value = mock_response({
        "ticket_id": "TKT-123",
        "reviews": [{"id": 1}],
    })

    result = client.get_reviews("TKT-123")

    assert len(result["reviews"]) == 1


def test_connection_error(client, session):
    session.request.side_effect = (
        requests.ConnectionError("offline")
    )

    with pytest.raises(
        APIError,
        match="Cannot connect",
    ):
        client.health()


def test_timeout(client, session):
    session.request.side_effect = (
        requests.Timeout("timeout")
    )

    with pytest.raises(
        APIError,
        match="timed out",
    ):
        client.health()


def test_http_error(client, session):
    response = mock_response(
        {"detail": "Ticket not found"},
        status=404,
    )

    response.raise_for_status.side_effect = (
        requests.HTTPError(
            "404 Not Found",
            response=response,
        )
    )

    session.request.return_value = response

    with pytest.raises(
        APIError,
        match="Ticket not found",
    ):
        client.get_ticket("UNKNOWN")
