
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "supportiq.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        DB_PATH,
        timeout=10,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")

    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT NOT NULL UNIQUE,
                message TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                CHECK (
                    category IN (
                        'billing', 'delivery',
                        'account', 'technical'
                    )
                ),
                CHECK (
                    priority IN ('low', 'medium', 'high')
                )
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT NOT NULL,
                predicted_category TEXT NOT NULL,
                confidence REAL NOT NULL,
                assigned_team TEXT NOT NULL,
                needs_human_review INTEGER NOT NULL,
                model_version TEXT NOT NULL,
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (ticket_id)
                    REFERENCES tickets(ticket_id),

                CHECK (confidence >= 0 AND confidence <= 1),
                CHECK (needs_human_review IN (0, 1))
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_predictions_ticket
            ON predictions(ticket_id)
        """)


        connection.execute("""
            CREATE TABLE IF NOT EXISTS ticket_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT NOT NULL,
                previous_category TEXT NOT NULL,
                new_category TEXT NOT NULL,
                previous_priority TEXT NOT NULL,
                new_priority TEXT NOT NULL,
                previous_status TEXT NOT NULL,
                new_status TEXT NOT NULL,
                reviewer_note TEXT NOT NULL,
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (ticket_id)
                    REFERENCES tickets(ticket_id)
            )
        """)


        connection.commit()


def create_ticket(ticket_id, message, decision):
    status = (
        "pending_review"
        if decision.needs_human_review
        else "open"
    )

    with get_connection() as connection:
        # Both inserts share one transaction.
        connection.execute("""
            INSERT INTO tickets (
                ticket_id, message, category,
                priority, status
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            ticket_id,
            message,
            decision.category,
            decision.priority,
            status,
        ))

        connection.execute("""
            INSERT INTO predictions (
                ticket_id,
                predicted_category,
                confidence,
                assigned_team,
                needs_human_review,
                model_version
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            ticket_id,
            decision.category,
            decision.confidence,
            decision.assigned_team,
            int(decision.needs_human_review),
            decision.model_version,
        ))

        connection.commit()

    return get_ticket(ticket_id)


def get_ticket(ticket_id):
    with get_connection() as connection:
        row = connection.execute("""
            SELECT
                t.ticket_id,
                t.message,
                t.category,
                t.priority,
                t.status,
                t.created_at,
                p.predicted_category,
                p.confidence,
                p.assigned_team,
                p.needs_human_review,
                p.model_version
            FROM tickets t
            JOIN predictions p
              ON t.ticket_id = p.ticket_id
            WHERE t.ticket_id = ?
            ORDER BY p.id DESC
            LIMIT 1
        """, (ticket_id,)).fetchone()

    return dict(row) if row else None


def list_tickets(limit=20, offset=0, status=None):
    filters = ""
    parameters = []

    if status:
        filters = "WHERE t.status = ?"
        parameters.append(status)

    with get_connection() as connection:
        total = connection.execute(
            f"SELECT COUNT(*) FROM tickets t {filters}",
            parameters,
        ).fetchone()[0]

        rows = connection.execute(f"""
            SELECT t.ticket_id
            FROM tickets t
            {filters}
            ORDER BY t.id DESC
            LIMIT ? OFFSET ?
        """, (*parameters, limit, offset)).fetchall()

    tickets = []

    for row in rows:
        ticket = get_ticket(row["ticket_id"])
        if ticket:
            tickets.append(ticket)

    return total, tickets



def update_ticket_review(
    ticket_id,
    category,
    priority,
    status,
    reviewer_note,
):
    with get_connection() as connection:
        previous = connection.execute("""
            SELECT category, priority, status
            FROM tickets
            WHERE ticket_id = ?
        """, (ticket_id,)).fetchone()

        if previous is None:
            return None

        connection.execute("""
            UPDATE tickets
            SET category = ?,
                priority = ?,
                status = ?
            WHERE ticket_id = ?
        """, (
            category,
            priority,
            status,
            ticket_id,
        ))

        connection.execute("""
            INSERT INTO ticket_reviews (
                ticket_id,
                previous_category,
                new_category,
                previous_priority,
                new_priority,
                previous_status,
                new_status,
                reviewer_note
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket_id,
            previous["category"],
            category,
            previous["priority"],
            priority,
            previous["status"],
            status,
            reviewer_note,
        ))

        connection.commit()

    return get_ticket(ticket_id)


def get_ticket_reviews(ticket_id):
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT *
            FROM ticket_reviews
            WHERE ticket_id = ?
            ORDER BY id DESC
        """, (ticket_id,)).fetchall()

    return [dict(row) for row in rows]


