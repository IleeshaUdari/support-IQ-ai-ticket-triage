
import pytest

from app.classifier import predict_ticket, load_model
from scripts.train import (
    load_dataset,
    split_dataset,
    normalize_template,
    CATEGORIES,
)


def test_model_loads():
    model = load_model()

    assert model is not None
    assert hasattr(model, "predict")
    assert hasattr(model, "predict_proba")


def test_prediction_schema():
    result = predict_ticket(
        "I was charged twice for my order"
    )

    assert isinstance(result, dict)

    assert "category" in result
    assert "confidence" in result
    assert "category_scores" in result
    assert "model_version" in result


def test_category_is_valid():
    result = predict_ticket(
        "I cannot access my account"
    )

    assert result["category"] in CATEGORIES


def test_confidence_range():
    result = predict_ticket(
        "The website is not loading"
    )

    assert 0 <= result["confidence"] <= 1


def test_probabilities_sum_to_one():
    result = predict_ticket(
        "My delivery has not arrived"
    )

    total = sum(result["category_scores"].values())

    assert total == pytest.approx(1.0, abs=0.001)


def test_empty_message_rejected():
    with pytest.raises(ValueError):
        predict_ticket("   ")


def test_non_string_rejected():
    with pytest.raises(TypeError):
        predict_ticket(None)


def test_oversized_message_rejected():
    with pytest.raises(ValueError):
        predict_ticket("a" * 5001)


def test_template_normalization():
    first = normalize_template(
        "I was charged twice for order 1234"
    )

    second = normalize_template(
        "I was charged twice for order 9876"
    )

    assert first == second


def test_no_template_leakage():
    df = load_dataset()
    train_df, test_df = split_dataset(df)

    train_groups = set(train_df["template_group"])
    test_groups = set(test_df["template_group"])

    assert train_groups.isdisjoint(test_groups)


def test_all_categories_in_both_splits():
    df = load_dataset()
    train_df, test_df = split_dataset(df)

    assert set(train_df["category"]) == set(CATEGORIES)
    assert set(test_df["category"]) == set(CATEGORIES)
