
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATASET = BASE_DIR / "data" / "raw" / "support_tickets.csv"

df = pd.read_csv(DATASET)

print("\nDataset Shape:")
print(df.shape)

print("\nFirst 5 Records:")
print(df.head())

print("\nCategory Distribution:")
print(df["category"].value_counts())

print("\nMissing Values:")
print(df.isnull().sum())

print("\nDuplicate Messages:")
print(df["message"].duplicated().sum())

print("\nUnique Messages:")
print(df["message"].nunique())

