
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]

RAW_FILE = BASE_DIR / "data" / "raw" / "support_tickets.csv"
CLEAN_FILE = BASE_DIR / "data" / "processed" / "clean_tickets.csv"

REQUIRED_COLUMNS = [
    "ticket_id",
    "message",
    "category",
    "priority",
]

VALID_CATEGORIES = {
    "billing",
    "delivery",
    "account",
    "technical",
}

VALID_PRIORITIES = {
    "low",
    "medium",
    "high",
}


def validate_dataset():
    print("Starting SupportIQ data validation...")

    df = pd.read_csv(RAW_FILE, dtype=str)

    # Validate schema
    missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing columns: {sorted(missing_columns)}"
        )

    if df.empty:
        raise ValueError("Dataset is empty")

    if df.columns.tolist() != REQUIRED_COLUMNS:
        raise ValueError("Unexpected dataset schema")

    original_count = len(df)

    # Normalize string fields
    for column in REQUIRED_COLUMNS:
        df[column] = df[column].fillna("").str.strip()

    df["category"] = df["category"].str.lower()
    df["priority"] = df["priority"].str.lower()

    # Reject incomplete records
    empty_values = (df[REQUIRED_COLUMNS] == "").any(axis=1)

    if empty_values.any():
        raise ValueError(
            f"Found {empty_values.sum()} incomplete records"
        )

    # Validate allowed categories
    invalid_categories = set(df["category"]) - VALID_CATEGORIES

    if invalid_categories:
        raise ValueError(
            f"Invalid categories: {sorted(invalid_categories)}"
        )

    # Validate allowed priorities
    invalid_priorities = set(df["priority"]) - VALID_PRIORITIES

    if invalid_priorities:
        raise ValueError(
            f"Invalid priorities: {sorted(invalid_priorities)}"
        )

    # Ticket IDs must be unique
    if df["ticket_id"].duplicated().any():
        raise ValueError("Duplicate ticket IDs detected")

    # Remove exact duplicate messages
    df["normalized_message"] = (
        df["message"]
        .str.lower()
        .str.replace(r"\s+", " ", regex=True)
    )

    df = df.drop_duplicates(
        subset=["normalized_message"],
        keep="first"
    )

    df = df.drop(columns=["normalized_message"])

    CLEAN_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(CLEAN_FILE, index=False)

    print("\nValidation completed successfully!")
    print(f"Original records: {original_count}")
    print(f"Clean records: {len(df)}")
    print(f"Duplicates removed: {original_count - len(df)}")
    print(f"Saved to: {CLEAN_FILE}")

    print("\nCategory distribution:")
    print(df["category"].value_counts())

    return df


if __name__ == "__main__":
    validate_dataset()
