
from app.database import get_connection, initialize_database


def check_database():
    initialize_database()

    with get_connection() as connection:
        tables = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name IN ('tickets', 'predictions')
            ORDER BY name
        """).fetchall()

        table_names = [row["name"] for row in tables]

        print("\nDatabase tables:")
        for name in table_names:
            print(f"- {name}")

        assert table_names == ["predictions", "tickets"], (
            "Required tables are missing"
        )

        print("\nDatabase verification passed!")


if __name__ == "__main__":
    check_database()
