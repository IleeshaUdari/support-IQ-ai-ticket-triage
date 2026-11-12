
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

DB_PATH = BASE_DIR / "data" / "supportiq.db"


def get_connection():
    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

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
                        'billing',
                        'delivery',
                        'account',
                        'technical'
                    )
                ),

                CHECK (
                    priority IN (
                        'low',
                        'medium',
                        'high'
                    )
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

        connection.commit()

    print(f"Database initialized: {DB_PATH}")


if __name__ == "__main__":
    initialize_database()
