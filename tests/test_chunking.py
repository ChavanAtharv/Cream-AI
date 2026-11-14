"""Tests for app.chunking (no real PDFs needed)."""

import json
from unittest.mock import patch

import pytest

from app.chunking import (
    build_chunks,
    chunk_text,
    read_text_sections,
)


def _words(count):
    return " ".join(f"w{i}" for i in range(count))


# ---- chunk_text ----------------------------------------------------------

def test_chunk_text_overlaps_and_covers_everything():
    chunks = chunk_text(_words(300), size=100, overlap=20)
    assert len(chunks) == 4
    assert chunks[1].split()[0] == "w80"  # next chunk starts 20 words early
    assert chunks[-1].split()[-1] == "w299"


def test_chunk_text_short_text_is_one_chunk():
    assert chunk_text(_words(100), size=100, overlap=20) == [_words(100)]


def test_chunk_text_ignores_near_empty_text():
    assert chunk_text("") == []
    assert chunk_text("12") == []


def test_chunk_text_rejects_bad_settings():
    for size, overlap in [(0, 0), (10, 10), (10, 20), (10, -1)]:
        with pytest.raises(ValueError):
            chunk_text(_words(50), size=size, overlap=overlap)


# ---- read_text_sections --------------------------------------------------

def test_read_text_sections_splits_on_headings(tmp_path):
    path = tmp_path / "scheme.txt"
    path.write_text("# Benefits\nRs 6000 a year\n\n# Eligibility\nSmall farmers\n")
    assert read_text_sections(path) == [
        (1, "# Benefits Rs 6000 a year"),
        (2, "# Eligibility Small farmers"),
    ]


def test_read_text_sections_without_headings_is_one_section(tmp_path):
    path = tmp_path / "plain.txt"
    path.write_text("just some plain text\nacross two lines\n")
    assert len(read_text_sections(path)) == 1


# ---- build_chunks --------------------------------------------------------

def test_build_chunks_keeps_title_source_and_page(tmp_path):
    (tmp_path / "scheme.txt").write_text("# One\n" + _words(40))
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "scheme.txt": {
                    "title": "Test Scheme",
                    "source_url": "https://example.gov.in/a",
                    "scheme_id": "TEST",
                }
            }
        )
    )
    chunks = build_chunks(tmp_path, size=100, overlap=20)
    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk["id"] == "scheme-p1-c1"
    assert chunk["title"] == "Test Scheme"
    assert chunk["source"] == "https://example.gov.in/a"
    assert chunk["page"] == 1
    assert chunk["scheme_id"] == "TEST"


def test_build_chunks_file_missing_from_manifest_gets_fallbacks(tmp_path):
    (tmp_path / "notes.txt").write_text(_words(40))
    chunks = build_chunks(tmp_path)
    assert chunks[0]["title"] == "notes"
    assert chunks[0]["source"] == "unknown"


def test_build_chunks_uses_page_numbers_for_pdfs(tmp_path):
    (tmp_path / "guide.pdf").write_bytes(b"placeholder")
    pages = [(1, _words(30)), (3, _words(30))]
    with patch("app.chunking.read_pdf_pages", return_value=pages):
        chunks = build_chunks(tmp_path)
    assert [chunk["page"] for chunk in chunks] == [1, 3]


def test_build_chunks_skips_unreadable_pdf_and_other_files(tmp_path):
    (tmp_path / "broken.pdf").write_bytes(b"this is not a pdf")
    (tmp_path / "image.png").write_bytes(b"x")
    (tmp_path / "ok.txt").write_text(_words(30))
    chunks = build_chunks(tmp_path)
    assert {chunk["file"] for chunk in chunks} == {"ok.txt"}
