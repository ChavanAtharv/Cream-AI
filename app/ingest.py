
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_FILE = PROJECT_ROOT / "data" / "records.json"


def clean_record(raw):
    """Convert a raw scheme record into the required format."""

    if not isinstance(raw, dict):
        raise ValueError("Record must be a dictionary")

    scheme_name = raw.get("scheme_name")
    source_url = raw.get("source_url")

    if not isinstance(scheme_name, str) or not scheme_name.strip():
        raise ValueError("Missing or invalid scheme_name")

    if not isinstance(source_url, str) or not source_url.strip():
        raise ValueError("Missing or invalid source_url")

    ministry = raw.get("ministry")
    if ministry is not None and not isinstance(ministry, str):
        raise ValueError("Invalid ministry")

    benefit = raw.get("benefit")
    eligibility = raw.get("eligibility")
    documents = raw.get("documents_required", [])

    if benefit is not None and not isinstance(benefit, str):
        raise ValueError("Invalid benefit")

    if eligibility is not None and not isinstance(eligibility, str):
        raise ValueError("Invalid eligibility")

    if not isinstance(documents, list):
        raise ValueError("documents_required must be a list")

    if not all(isinstance(item, str) for item in documents):
        raise ValueError("Documents must contain only strings")

    return {
        "scheme_name": scheme_name.strip(),
        "ministry": ministry.strip() if ministry else None,
        "benefit": benefit.strip() if benefit else None,
        "eligibility": eligibility.strip() if eligibility else None,
        "documents_required": [
            document.strip() for document in documents if document.strip()
        ],
        "source_url": source_url.strip()
    }


def ingest():
    records = []

    for file_path in RAW_DIR.glob("*.json"):
        try:
            with file_path.open("r", encoding="utf-8") as file:
                raw_data = json.load(file)

            # Support either one record or a list of records.
            raw_records = raw_data if isinstance(raw_data, list) else [raw_data]

            for raw_record in raw_records:
                try:
                    cleaned = clean_record(raw_record)
                    records.append(cleaned)
                    print(f"Processed: {cleaned['scheme_name']}")

                except (ValueError, TypeError) as error:
                    print(f"Skipped invalid record in {file_path.name}: {error}")

        except (OSError, json.JSONDecodeError) as error:
            print(f"Could not read {file_path.name}: {error}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=4, ensure_ascii=False)

    print(f"\nIngestion completed.")
    print(f"Valid records: {len(records)}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    ingest()

