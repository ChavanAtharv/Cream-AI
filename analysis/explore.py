
import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "records.json"


def explore_data():
    if not DATA_FILE.exists():
        print("Error: records.json not found. Run ingestion first.")
        return

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            records = json.load(file)

        if not isinstance(records, list) or not records:
            print("No records available for analysis.")
            return

        df = pd.DataFrame(records)

        print("\n--- SchemeSaathi Data Exploration ---")

        # Fact 1: Total number of schemes
        print(f"\n1. Total schemes: {len(df)}")

        # Fact 2: Number of schemes under each ministry
        print("\n2. Schemes by ministry:")
        print(df["ministry"].fillna("Unknown").value_counts().to_string())

        # Fact 3: Missing values in each field
        print("\n3. Missing values by field:")
        print(df.isnull().sum().to_string())

    except (OSError, json.JSONDecodeError) as error:
        print(f"Could not read records: {error}")


if __name__ == "__main__":
    explore_data()
