
from pathlib import Path
import re
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = BASE_DIR / "data" / "processed" / "clean_tickets.csv"
TRAIN_FILE = BASE_DIR / "data" / "processed" / "train.csv"
TEST_FILE = BASE_DIR / "data" / "processed" / "test.csv"

CATEGORIES = ["account", "billing", "delivery", "technical"]


def normalize_template(message):
    """
    Replace numbers to identify messages that
    originate from the same synthetic template.
    """
    text = message.strip().lower()
    text = re.sub(r"\d+", "<NUM>", text)
    text = re.sub(r"\s+", " ", text)
    return text


def prepare_data():
    print("\nSupportIQ - Data Preparation")
    print("=" * 40)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Clean dataset not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required = {"ticket_id", "message", "category", "priority"}

    if not required.issubset(df.columns):
        raise ValueError("Dataset is missing required columns")

    if df.empty:
        raise ValueError("Dataset is empty")

    if df[list(required)].isna().any().any():
        raise ValueError("Dataset contains missing values")

    df["category"] = df["category"].str.strip().str.lower()

    if set(df["category"]) != set(CATEGORIES):
        raise ValueError("Unexpected support categories")

    # Identify original synthetic message families.
    df["template_group"] = df["message"].apply(
        normalize_template
    )

    # Ensure each template has only one correct category.
    conflicts = df.groupby("template_group")["category"].nunique()

    if (conflicts > 1).any():
        raise ValueError("Conflicting labels found")

    # Select one complete template per category for testing.
    test_groups = []

    for category in CATEGORIES:
        category_groups = sorted(
            df.loc[
                df["category"] == category,
                "template_group"
            ].unique()
        )

        if len(category_groups) < 2:
            raise ValueError(
                f"Not enough templates for {category}"
            )

        test_groups.append(category_groups[-1])

    is_test = df["template_group"].isin(test_groups)

    train_df = df.loc[~is_test].copy()
    test_df = df.loc[is_test].copy()

    # Verify that no template appears in both datasets.
    train_groups = set(train_df["template_group"])
    test_groups = set(test_df["template_group"])

    assert train_groups.isdisjoint(test_groups)

    assert set(train_df["category"]) == set(CATEGORIES)
    assert set(test_df["category"]) == set(CATEGORIES)

    # Remove the helper column before saving.
    train_df = train_df.drop(columns=["template_group"])
    test_df = test_df.drop(columns=["template_group"])

    TRAIN_FILE.parent.mkdir(parents=True, exist_ok=True)

    train_df.to_csv(TRAIN_FILE, index=False)
    test_df.to_csv(TEST_FILE, index=False)

    print(f"Total records: {len(df)}")
    print(f"Training records: {len(train_df)}")
    print(f"Testing records: {len(test_df)}")

    print("\nTraining category distribution:")
    print(train_df["category"].value_counts())

    print("\nTesting category distribution:")
    print(test_df["category"].value_counts())

    print("\nNo template leakage detected.")
    print(f"Training file saved: {TRAIN_FILE}")
    print(f"Testing file saved: {TEST_FILE}")


if __name__ == "__main__":
    prepare_data()
