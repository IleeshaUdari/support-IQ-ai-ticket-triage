
from pathlib import Path
from datetime import datetime, timezone
import json
import re

import joblib
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "data" / "processed" / "clean_tickets.csv"
MODEL_DIR = BASE_DIR / "models"
REPORT_DIR = BASE_DIR / "reports"

MODEL_PATH = MODEL_DIR / "ticket_classifier.joblib"
METRICS_PATH = REPORT_DIR / "metrics.json"
CONFUSION_PATH = REPORT_DIR / "confusion_matrix.csv"
SPLIT_PATH = REPORT_DIR / "test_predictions.csv"
METADATA_PATH = MODEL_DIR / "model_metadata.json"

CATEGORIES = [
    "account",
    "billing",
    "delivery",
    "technical",
]

MODEL_VERSION = "1.0.0"


def normalize_template(message: str) -> str:
    """
    Replace numeric identifiers so messages generated
    from the same template belong to the same group.
    """
    text = message.strip().lower()
    text = re.sub(r"\d+", "<NUM>", text)
    text = re.sub(r"\s+", " ", text)
    return text


def load_dataset() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}\n"
            "Run python scripts/validate_data.py first."
        )

    df = pd.read_csv(DATA_PATH)

    required = {
        "ticket_id",
        "message",
        "category",
        "priority",
    }

    if not required.issubset(df.columns):
        raise ValueError("Dataset has missing columns")

    if df.empty:
        raise ValueError("Dataset is empty")

    if df[list(required)].isna().any().any():
        raise ValueError("Dataset contains missing values")

    df["message"] = df["message"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip().str.lower()

    if (df["message"] == "").any():
        raise ValueError("Dataset contains empty messages")

    if not set(df["category"]).issubset(CATEGORIES):
        raise ValueError("Dataset contains unknown categories")

    if df["ticket_id"].duplicated().any():
        raise ValueError("Duplicate ticket IDs found")

    return df


def split_dataset(df: pd.DataFrame):
    """
    Hold out one complete message-template family
    from each category.

    The held-out template is selected deterministically
    using sorted template names.
    """
    df = df.copy()

    df["template_group"] = df["message"].apply(
        normalize_template
    )

    # A template must not have conflicting labels.
    conflicts = df.groupby("template_group")["category"].nunique()

    if (conflicts > 1).any():
        raise ValueError(
            "Some message templates have conflicting categories"
        )

    test_groups = []

    for category in CATEGORIES:
        groups = sorted(
            df.loc[
                df["category"] == category,
                "template_group"
            ].unique()
        )

        if len(groups) < 2:
            raise ValueError(
                f"Not enough distinct templates for {category}"
            )

        # Reserve one full template family per category.
        test_groups.append(groups[-1])

    is_test = df["template_group"].isin(test_groups)

    train_df = df.loc[~is_test].copy()
    test_df = df.loc[is_test].copy()

    train_groups = set(train_df["template_group"])
    test_groups = set(test_df["template_group"])

    assert train_groups.isdisjoint(test_groups)
    assert set(train_df["category"]) == set(CATEGORIES)
    assert set(test_df["category"]) == set(CATEGORIES)

    return train_df, test_df


def build_pipeline():
    return Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                lowercase=True,
                strip_accents="unicode",
                ngram_range=(1, 2),
                max_features=5000,
                sublinear_tf=True,
            )
        ),
        (
            "classifier",
            LogisticRegression(
                max_iter=1000,
                random_state=42,
            )
        ),
    ])


def train():
    print("\nSupportIQ AI - Model Training")
    print("=" * 45)

    df = load_dataset()

    train_df, test_df = split_dataset(df)

    X_train = train_df["message"]
    y_train = train_df["category"]

    X_test = test_df["message"]
    y_test = test_df["category"]

    print(f"Total records: {len(df)}")
    print(f"Training records: {len(train_df)}")
    print(f"Testing records: {len(test_df)}")

    print("\nTraining classifier...")

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    print("Training completed.")

    predictions = pipeline.predict(X_test)

    probabilities = pipeline.predict_proba(X_test)
    confidence = probabilities.max(axis=1)

    accuracy = accuracy_score(y_test, predictions)
    macro_f1 = f1_score(
        y_test,
        predictions,
        average="macro",
        zero_division=0,
    )

    report = classification_report(
        y_test,
        predictions,
        labels=CATEGORIES,
        output_dict=True,
        zero_division=0,
    )

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=CATEGORIES,
    )

    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            predictions,
            labels=CATEGORIES,
            zero_division=0,
        )
    )

    print(f"Accuracy: {accuracy:.4f}")
    print(f"Macro F1: {macro_f1:.4f}")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(pipeline, MODEL_PATH)

    metrics = {
        "model_version": MODEL_VERSION,
        "dataset_type": "synthetic",
        "split_strategy": "template_family_holdout",
        "total_samples": len(df),
        "training_samples": len(train_df),
        "testing_samples": len(test_df),
        "accuracy": float(accuracy),
        "macro_f1": float(macro_f1),
        "classification_report": report,
        "labels": CATEGORIES,
    }

    with METRICS_PATH.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    cm_df = pd.DataFrame(
        matrix,
        index=CATEGORIES,
        columns=CATEGORIES,
    )
    cm_df.to_csv(CONFUSION_PATH)

    results = test_df[
        ["ticket_id", "message", "category"]
    ].copy()

    results["predicted_category"] = predictions
    results["confidence"] = confidence
    results["correct"] = (
        results["category"] == results["predicted_category"]
    )

    results.to_csv(SPLIT_PATH, index=False)

    metadata = {
        "model_version": MODEL_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model_type": "TF-IDF + Logistic Regression",
        "categories": CATEGORIES,
        "training_samples": len(train_df),
        "test_samples": len(test_df),
        "evaluation": "synthetic template-family holdout",
        "confidence_calibrated": False,
    }

    with METADATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("\nSaved artifacts:")
    print(f"Model: {MODEL_PATH}")
    print(f"Metrics: {METRICS_PATH}")
    print(f"Confusion matrix: {CONFUSION_PATH}")
    print(f"Test predictions: {SPLIT_PATH}")
    print(f"Metadata: {METADATA_PATH}")

    return pipeline


if __name__ == "__main__":
    train()
