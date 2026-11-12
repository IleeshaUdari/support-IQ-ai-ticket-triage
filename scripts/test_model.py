
from app.classifier import predict_ticket


def main():
    sample_messages = [
        "I was charged twice for my subscription.",
        "My package arrived damaged.",
        "I cannot access my account.",
        "The application crashes every time I log in.",
        "I need help with something.",
    ]

    print("\nSupportIQ AI - Inference Demo")
    print("=" * 50)

    for message in sample_messages:
        result = predict_ticket(message)

        print(f"\nMessage: {message}")
        print(f"Category: {result['category']}")
        print(f"Model score: {result['confidence']:.2%}")
        print(f"Model version: {result['model_version']}")
        print("-" * 50)


if __name__ == "__main__":
    main()
