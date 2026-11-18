"""Tests for app.tools."""

import json

import pytest

from app.tools import ToolError, ask_documents, compare_schemes, find_scheme, load_scheme_records

RECORDS = [
    {"id": "PM_KISAN", "scheme_name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
     "benefit": "Rs 6000 a year", "eligibility": "Landholding farmers | exclusions apply",
     "documents_required": ["Aadhaar", "Land papers"], "source_url": "https://example.gov.in/kisan"},
    {"id": "APY", "scheme_name": "Atal Pension Yojana (APY)",
     "benefit": "Monthly pension", "eligibility": "Age 18 to 40",
     "documents_required": [], "source_url": "https://example.gov.in/apy"},
    {"id": "PMAY_G", "scheme_name": "Pradhan Mantri Awaas Yojana - Gramin (PMAY-G)",
     "benefit": "Housing grant", "eligibility": "Rural houseless", "documents_required": ["Bank account"],
     "source_url": "https://example.gov.in/pmayg"},
    {"id": "PMAY_U", "scheme_name": "Pradhan Mantri Awas Yojana - Urban (PMAY-U)",
     "benefit": "Housing subsidy", "eligibility": "Urban households", "documents_required": [],
     "source_url": None},
]


# ---- find_scheme ---------------------------------------------------------

def test_find_scheme_by_id_acronym_and_loose_spelling():
    assert find_scheme("APY", RECORDS)["id"] == "APY"
    assert find_scheme("pm kisan", RECORDS)["id"] == "PM_KISAN"
    assert find_scheme("PM_KISAN", RECORDS)["id"] == "PM_KISAN"
    assert find_scheme("atal pension yojana", RECORDS)["id"] == "APY"


def test_find_scheme_ambiguous_and_unknown():
    with pytest.raises(ToolError) as ambiguous:
        find_scheme("PMAY", RECORDS)
    assert "PMAY-G" in str(ambiguous.value) and "PMAY-U" in str(ambiguous.value)
    with pytest.raises(ToolError) as unknown:
        find_scheme("free laptop scheme", RECORDS)
    assert "Known schemes" in str(unknown.value)
    with pytest.raises(ToolError):
        find_scheme("  ", RECORDS)


# ---- compare_schemes -----------------------------------------------------

def test_compare_schemes_builds_markdown_table():
    table = compare_schemes(["PM-KISAN", "APY"], records=RECORDS)
    lines = table.splitlines()
    assert lines[0] == "| | Pradhan Mantri Kisan Samman Nidhi (PM-KISAN) | Atal Pension Yojana (APY) |"
    assert lines[1] == "|---|---|---|"
    assert "| Benefit | Rs 6000 a year | Monthly pension |" in lines
    assert "| Documents required | Aadhaar; Land papers | Not specified |" in lines
    assert "| Apply link | https://example.gov.in/kisan | https://example.gov.in/apy |" in lines
    assert len(lines) == 6


def test_compare_schemes_escapes_pipes_and_handles_missing_link():
    table = compare_schemes(["PM-KISAN", "PMAY-U"], records=RECORDS)
    assert "Landholding farmers / exclusions apply" in table
    assert "| Apply link | https://example.gov.in/kisan | Not available |" in table


def test_compare_schemes_accepts_up_to_four():
    table = compare_schemes(["PM-KISAN", "APY", "PMAY-G", "PMAY-U"], records=RECORDS)
    assert table.splitlines()[1] == "|---|---|---|---|---|"


def test_compare_schemes_rejects_bad_input():
    for bad in ["APY", None, ["APY"], ["a", "b", "c", "d", "e"], ["APY", 5]]:
        with pytest.raises(ToolError):
            compare_schemes(bad, records=RECORDS)
    with pytest.raises(ToolError):
        compare_schemes(["APY", "atal pension"], records=RECORDS)  # same scheme twice
    with pytest.raises(ToolError):
        compare_schemes(["APY", "nonexistent scheme"], records=RECORDS)


# ---- load_scheme_records -------------------------------------------------

def test_load_scheme_records_reads_json_and_reports_problems(tmp_path):
    good = tmp_path / "records.json"
    good.write_text(json.dumps(RECORDS))
    assert len(load_scheme_records(good)) == 4
    with pytest.raises(ToolError):
        load_scheme_records(tmp_path / "missing.json")
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    with pytest.raises(ToolError):
        load_scheme_records(bad)
    wrong = tmp_path / "wrong.json"
    wrong.write_text('{"a": 1}')
    with pytest.raises(ToolError):
        load_scheme_records(wrong)


# ---- ask_documents -------------------------------------------------------

def test_ask_documents_adds_sources_to_the_answer():
    def fake(question):
        return {"answer": "It is Rs 6000.", "citations": [
            {"title": "FAQ", "page": 2, "source": "https://example.gov.in/faq"}]}

    text = ask_documents("annual benefit?", answer_fn=fake)
    assert text == "It is Rs 6000.\nSources: FAQ (page 2) https://example.gov.in/faq"


def test_ask_documents_dont_know_has_no_sources_and_rejects_blank():
    text = ask_documents("deadline?", answer_fn=lambda q: {"answer": "I don't know.", "citations": []})
    assert text == "I don't know."
    with pytest.raises(ToolError):
        ask_documents("  ", answer_fn=lambda q: {})
