"""Data model for a SchemeSaathi scheme record."""

from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class Record:
    """One government scheme, with the fields used across the project."""

    scheme_name: str
    source_url: str
    ministry: Optional[str] = None
    benefit: Optional[str] = None
    eligibility: Optional[str] = None
    documents_required: list[str] = field(default_factory=list)
    id: Optional[str] = None
    category: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.scheme_name, str) or not self.scheme_name.strip():
            raise ValueError("scheme_name must be a non-empty string")
        if not isinstance(self.source_url, str) or not self.source_url.strip():
            raise ValueError("source_url must be a non-empty string")
        if not isinstance(self.documents_required, list):
            raise ValueError("documents_required must be a list")

    @classmethod
    def from_dict(cls, data):
        """Build a Record from a dictionary, ignoring unknown keys."""
        if not isinstance(data, dict):
            raise ValueError("Record data must be a dictionary")
        known = cls.__dataclass_fields__.keys()
        return cls(**{key: value for key, value in data.items() if key in known})

    def to_dict(self):
        """Return the record as a plain dictionary (for JSON or the API)."""
        return asdict(self)
