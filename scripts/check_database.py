
from app.database import initialize_database, get_connection


def check_database():
    initialize_database()

    connection = get_connection()

    try:
        cursor = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)

        tables = [row["name"] for row in cursor.fetchall()]

        print("\nSupportIQ Database Verification")
        print("=" * 40)

        for table in tables:
            print(f"Table found: {table}")

        required_tables = {
            "tickets",
            "predictions",
            "ticket_reviews",
        }

        missing = required_tables - set(tables)

        if missing:
            raise RuntimeError(
                f"Missing tables: {sorted(missing)}"
            )

        print("\nAll required database tables exist!")
        print("Database verification PASSED!")

    finally:
        connection.close()


if __name__ == "__main__":
    check_database()
