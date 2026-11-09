"""Tests for app.models, app.ingest and app.fetch (no real network calls)."""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from app.fetch import FetchError, download_all, extension_for, fetch_document
from app.ingest import clean_record, ingest
from app.models import Record


# ---- Record --------------------------------------------------------------

def test_record_from_dict_ignores_unknown_keys():
    record = Record.from_dict(
        {"scheme_name": "A", "source_url": "https://x.gov.in", "extra": 1}
    )
    assert record.scheme_name == "A"
    assert record.documents_required == []


def test_record_requires_scheme_name_and_url():
    with pytest.raises(ValueError):
        Record(scheme_name="  ", source_url="https://x.gov.in")
    with pytest.raises(ValueError):
        Record(scheme_name="A", source_url="")


def test_record_to_dict_round_trip():
    data = {"scheme_name": "A", "source_url": "https://x.gov.in", "ministry": "M"}
    assert Record.from_dict(data).to_dict()["ministry"] == "M"


# ---- ingest --------------------------------------------------------------

def test_clean_record_strips_and_filters():
    record = clean_record(
        {
            "scheme_name": "  PM-KISAN ",
            "source_url": " https://x.gov.in ",
            "documents_required": [" Aadhaar ", "  "],
        }
    )
    assert record.scheme_name == "PM-KISAN"
    assert record.documents_required == ["Aadhaar"]
    assert record.ministry is None


@pytest.mark.parametrize(
    "bad",
    [
        None,
        {"source_url": "https://x.gov.in"},
        {"scheme_name": "A"},
        {"scheme_name": "A", "source_url": "u", "documents_required": "Aadhaar"},
        {"scheme_name": "A", "source_url": "u", "documents_required": [1]},
        {"scheme_name": "A", "source_url": "u", "benefit": 5},
    ],
)
def test_clean_record_rejects_bad_rows(bad):
    with pytest.raises(ValueError):
        clean_record(bad)


def test_ingest_skips_bad_rows_and_files(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    good = {"scheme_name": "A", "source_url": "https://x.gov.in"}
    (raw / "one.json").write_text(json.dumps([good, {"scheme_name": ""}]))
    (raw / "broken.json").write_text("{not json")
    out = tmp_path / "out" / "records.json"

    records = ingest(raw_dir=raw, output_file=out)

    assert [r["scheme_name"] for r in records] == ["A"]
    assert json.loads(out.read_text())[0]["scheme_name"] == "A"


# ---- fetch ---------------------------------------------------------------

def _response(content=b"data", content_type="application/pdf"):
    response = MagicMock()
    response.content = content
    response.headers = {"Content-Type": content_type}
    response.raise_for_status.return_value = None
    return response


def test_extension_for():
    assert extension_for("application/pdf; charset=binary") == ".pdf"
    assert extension_for("text/html; charset=utf-8") == ".html"
    assert extension_for(None) == ".bin"


def test_fetch_document_saves_file(tmp_path):
    with patch("app.fetch.requests.get", return_value=_response()):
        path = fetch_document("doc", "https://x.gov.in/a", dest_dir=tmp_path)
    assert path.name == "doc.pdf"
    assert path.read_bytes() == b"data"


@pytest.mark.parametrize(
    "error",
    [
        requests.exceptions.Timeout(),
        requests.exceptions.ConnectionError(),
        requests.exceptions.HTTPError("404"),
    ],
)
def test_fetch_document_wraps_request_errors(tmp_path, error):
    with patch("app.fetch.requests.get", side_effect=error):
        with pytest.raises(FetchError):
            fetch_document("doc", "https://x.gov.in/a", dest_dir=tmp_path)


def test_fetch_document_rejects_empty_response(tmp_path):
    with patch("app.fetch.requests.get", return_value=_response(content=b"")):
        with pytest.raises(FetchError):
            fetch_document("doc", "https://x.gov.in/a", dest_dir=tmp_path)


def test_download_all_continues_after_failure(tmp_path):
    def fake_get(url, **kwargs):
        if "bad" in url:
            raise requests.exceptions.Timeout()
        return _response()

    docs = {"good": "https://x.gov.in/good", "bad": "https://x.gov.in/bad"}
    with patch("app.fetch.requests.get", side_effect=fake_get):
        saved, failed = download_all(docs, dest_dir=tmp_path)

    assert list(saved) == ["good"]
    assert "bad" in failed

def test_records_json_has_complete_records():
    from pathlib import Path

    path = Path(__file__).resolve().parent.parent / "data" / "records.json"
    records = json.loads(path.read_text(encoding="utf-8"))
    assert len(records) >= 5
    for record in records:
        assert record["id"] and record["category"] and record["ministry"]
