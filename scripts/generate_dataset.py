
from pathlib import Path
import csv
import random

random.seed(42)

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT = BASE_DIR / "data" / "raw" / "support_tickets.csv"

templates = {
    "billing": [
        ("I was charged twice for order {id}", "high"),
        ("My refund for order {id} has not arrived", "medium"),
        ("Please send the invoice for order {id}", "low"),
        ("My payment for order {id} was declined", "medium"),
        ("The amount charged for order {id} is incorrect", "high"),
    ],
    "delivery": [
        ("Where is my package for order {id}?", "medium"),
        ("My order {id} has not arrived", "medium"),
        ("Order {id} was delivered to the wrong address", "high"),
        ("My package for order {id} arrived damaged", "high"),
        ("Please update the delivery address for order {id}", "medium"),
    ],
    "account": [
        ("I cannot log into my account {id}", "medium"),
        ("I forgot my password for account {id}", "medium"),
        ("Someone accessed my account {id} without permission", "high"),
        ("Please update my email address for account {id}", "low"),
        ("My account {id} has been locked", "high"),
    ],
    "technical": [
        ("The application crashes when I open page {id}", "high"),
        ("The website shows error code {id}", "high"),
        ("The dashboard is not loading for user {id}", "medium"),
        ("I cannot upload a document with reference {id}", "medium"),
        ("The mobile application freezes on screen {id}", "high"),
    ],
}

records = []
ticket_number = 1

for category, examples in templates.items():
    for _ in range(75):
        message_template, priority = random.choice(examples)

        message = message_template.format(
            id=random.randint(1000, 9999)
        )

        records.append({
            "ticket_id": f"T{ticket_number:04d}",
            "message": message,
            "category": category,
            "priority": priority,
        })

        ticket_number += 1

random.shuffle(records)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=["ticket_id", "message", "category", "priority"]
    )
    writer.writeheader()
    writer.writerows(records)

print(f"Generated {len(records)} synthetic support tickets.")
print(f"Dataset saved to: {OUTPUT}")
