"""Clean raw scheme JSON files in data/raw/ into data/records.json.

Run from the project root:
    python -m app.ingest
"""

import json
from pathlib import Path

from app.models import Record

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_FILE = PROJECT_ROOT / "data" / "records.json"


def _optional_text(raw, key):
    """Return a stripped string for an optional text field, or None."""
    value = raw.get(key)
    if value is not None and not isinstance(value, str):
        raise ValueError(f"Invalid {key}")
    if not value:
        return None
    return value.strip() or None


def clean_record(raw):
    """Convert a raw scheme record into a validated Record."""
    if not isinstance(raw, dict):
        raise ValueError("Record must be a dictionary")

    scheme_name = raw.get("scheme_name")
    source_url = raw.get("source_url")
    if not isinstance(scheme_name, str) or not scheme_name.strip():
        raise ValueError("Missing or invalid scheme_name")
    if not isinstance(source_url, str) or not source_url.strip():
        raise ValueError("Missing or invalid source_url")

    documents = raw.get("documents_required", [])
    if not isinstance(documents, list):
        raise ValueError("documents_required must be a list")
    if not all(isinstance(item, str) for item in documents):
        raise ValueError("Documents must contain only strings")

    return Record(
        scheme_name=scheme_name.strip(),
        source_url=source_url.strip(),
        ministry=_optional_text(raw, "ministry"),
        benefit=_optional_text(raw, "benefit"),
        eligibility=_optional_text(raw, "eligibility"),
        documents_required=[doc.strip() for doc in documents if doc.strip()],
        id=_optional_text(raw, "id"),
        category=_optional_text(raw, "category"),
    )


def ingest(raw_dir=RAW_DIR, output_file=OUTPUT_FILE):
    """Read every JSON file in raw_dir and save the valid records."""
    records = []

    for file_path in sorted(Path(raw_dir).glob("*.json")):
        try:
            with file_path.open("r", encoding="utf-8") as file:
                raw_data = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            print(f"Could not read {file_path.name}: {error}")
            continue

        # Support either one record or a list of records.
        raw_records = raw_data if isinstance(raw_data, list) else [raw_data]

        for raw_record in raw_records:
            try:
                cleaned = clean_record(raw_record)
            except (ValueError, TypeError) as error:
                print(f"Skipped invalid record in {file_path.name}: {error}")
                continue
            records.append(cleaned.to_dict())
            print(f"Processed: {cleaned.scheme_name}")

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=4, ensure_ascii=False)

    print("\nIngestion completed.")
    print(f"Valid records: {len(records)}")
    print(f"Saved to: {output_file}")
    return records


if __name__ == "__main__":
    ingest()