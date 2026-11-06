"""Reusable functions for SchemeSaathi scheme records."""

from copy import deepcopy
from data.sample_records import schemes as DEFAULT_RECORDS


def load_records(source=None):
    """Load the default scheme dataset or a supplied collection."""
    return deepcopy(list(DEFAULT_RECORDS if source is None else source))


def search(records, keyword, fields=None):
    """Case-insensitive substring search across scheme record fields."""
    if not isinstance(keyword, str):
        raise TypeError("keyword must be a string")
    term = keyword.strip().casefold()
    if not term:
        return []

    fields = fields or (
        "scheme_name", "category", "ministry", "benefit", "eligibility", "tags"
    )
    results = []
    for record in records:
        for field in fields:
            value = record.get(field)
            if value is None:
                continue
            values = value if isinstance(value, (list, tuple, set)) else [value]
            if any(term in str(item).casefold() for item in values):
                results.append(record)
                break
    return results


def count_by(records, field="category"):
    """Count records grouped by the requested field."""
    if not isinstance(field, str) or not field.strip():
        raise ValueError("field must be a non-empty string")
    counts = {}
    for record in records:
        value = record.get(field)
        if value is None or value == "":
            value = "Unspecified"
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: str(item[0]).casefold()))


def get_by_id(records, scheme_id):
    """Find a record by ID; return None when it does not exist."""
    if scheme_id is None:
        return None
    target = str(scheme_id).strip().casefold()
    if not target:
        return None
    return next(
        (record for record in records
         if str(record.get("id", "")).casefold() == target),
        None,
    )
