
import os

import requests


DEFAULT_API_URL = "http://127.0.0.1:8000"


class APIError(Exception):
    """A dashboard-to-API request failed."""


class SupportIQClient:
    def __init__(self, base_url=None, session=None):
        url = base_url or os.getenv(
            "SUPPORTIQ_API_URL",
            DEFAULT_API_URL,
        )

        self.base_url = url.rstrip("/")
        self.session = session or requests.Session()

    def _request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"

        try:
            response = self.session.request(
                method,
                url,
                timeout=15,
                **kwargs,
            )
            response.raise_for_status()
            return response.json()

        except requests.Timeout as exc:
            raise APIError(
                "API request timed out."
            ) from exc

        except requests.ConnectionError as exc:
            raise APIError(
                "Cannot connect to SupportIQ API. "
                "Check that FastAPI is running."
            ) from exc

        except requests.HTTPError as exc:
            detail = response.text

            try:
                payload = response.json()
                detail = payload.get("detail", detail)
            except ValueError:
                pass

            raise APIError(
                f"API error {response.status_code}: {detail}"
            ) from exc

        except ValueError as exc:
            raise APIError(
                "The API returned invalid JSON."
            ) from exc

    def health(self):
        return self._request("GET", "/health")

    def get_tickets(
        self,
        limit=20,
        offset=0,
        status=None,
    ):
        params = {
            "limit": limit,
            "offset": offset,
        }

        if status:
            params["status"] = status

        return self._request(
            "GET",
            "/api/v1/tickets",
            params=params,
        )

    def get_all_tickets(self, status=None):
        """
        Retrieve all tickets using the existing
        FastAPI pagination endpoint.

        Suitable for a small portfolio dataset.
        """
        results = []
        offset = 0
        page_size = 100

        while True:
            page = self.get_tickets(
                limit=page_size,
                offset=offset,
                status=status,
            )

            batch = page["tickets"]
            results.extend(batch)

            offset += len(batch)

            if not batch or offset >= page["total"]:
                break

        return results

    def get_ticket(self, ticket_id):
        return self._request(
            "GET",
            f"/api/v1/tickets/{ticket_id}",
        )

    def create_ticket(self, message):
        return self._request(
            "POST",
            "/api/v1/tickets",
            json={"message": message},
        )

    def review_ticket(
        self,
        ticket_id,
        category,
        priority,
        status,
        reviewer_note,
    ):
        return self._request(
            "PATCH",
            f"/api/v1/tickets/{ticket_id}/review",
            json={
                "category": category,
                "priority": priority,
                "status": status,
                "reviewer_note": reviewer_note,
            },
        )

    def get_reviews(self, ticket_id):
        return self._request(
            "GET",
            f"/api/v1/tickets/{ticket_id}/reviews",
        )
