
from pathlib import Path
import json

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
REPORT_DIR = BASE_DIR / "reports"


def evaluate():
    metrics_path = REPORT_DIR / "metrics.json"
    confusion_path = REPORT_DIR / "confusion_matrix.csv"
    predictions_path = REPORT_DIR / "test_predictions.csv"

    for path in [
        metrics_path,
        confusion_path,
        predictions_path,
    ]:
        if not path.exists():
            raise FileNotFoundError(
                f"Missing report: {path}\n"
                "Run python -m scripts.train first."
            )

    with metrics_path.open("r", encoding="utf-8") as file:
        metrics = json.load(file)

    print("\nSUPPORTIQ AI - MODEL EVALUATION")
    print("=" * 45)

    print(f"Model Version: {metrics['model_version']}")
    print(f"Training Samples: {metrics['training_samples']}")
    print(f"Testing Samples: {metrics['testing_samples']}")

    print(f"\nAccuracy: {metrics['accuracy']:.2%}")
    print(f"Macro F1: {metrics['macro_f1']:.4f}")

    print("\nCLASSIFICATION REPORT")
    report = metrics["classification_report"]

    for category in metrics["labels"]:
        result = report[category]

        print(f"\nCategory: {category}")
        print(f"  Precision: {result['precision']:.4f}")
        print(f"  Recall:    {result['recall']:.4f}")
        print(f"  F1 Score:  {result['f1-score']:.4f}")
        print(f"  Support:   {result['support']}")

    print("\nCONFUSION MATRIX")
    confusion = pd.read_csv(
        confusion_path,
        index_col=0
    )
    print(confusion)

    print("\nINCORRECT PREDICTIONS")
    predictions = pd.read_csv(predictions_path)

    # Handle CSV boolean values explicitly.
    incorrect = predictions[
        predictions["correct"].astype(str).str.lower() == "false"
    ]

    if incorrect.empty:
        print("No incorrect predictions in this test set.")
    else:
        for _, row in incorrect.head(10).iterrows():
            print(f"\nMessage: {row['message']}")
            print(f"Actual: {row['category']}")
            print(f"Predicted: {row['predicted_category']}")
            print(f"Model score: {row['confidence']:.2%}")

    print(f"\nTotal incorrect: {len(incorrect)}")
    print("\nEvaluation completed.")


if __name__ == "__main__":
    evaluate()
