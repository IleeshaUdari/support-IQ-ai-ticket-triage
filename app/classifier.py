
from pathlib import Path
from functools import lru_cache

import joblib

BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = (
    BASE_DIR / "models" / "ticket_classifier.joblib"
)


@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Trained model not found. "
            "Run python -m scripts.train first."
        )

    # Only load artifacts created by trusted code.
    # Joblib files can execute code during loading.
    return joblib.load(MODEL_PATH)


def predict_ticket(message: str) -> dict:
    if not isinstance(message, str):
        raise TypeError("Message must be a string")

    message = message.strip()

    if not message:
        raise ValueError("Message cannot be empty")

    if len(message) > 5000:
        raise ValueError(
            "Message cannot exceed 5000 characters"
        )

    model = load_model()

    predicted_category = str(
        model.predict([message])[0]
    )

    probabilities = model.predict_proba([message])[0]
    categories = model.classes_

    category_scores = {
        str(category): round(float(probability), 4)
        for category, probability in zip(
            categories, probabilities
        )
    }

    confidence = float(
        max(probabilities)
    )

    return {
        "category": predicted_category,
        "confidence": round(confidence, 4),
        "category_scores": category_scores,
        "model_version": "1.0.0",
    }
