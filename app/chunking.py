"""Split scheme documents into small chunks that keep source, page and title.

Documents live in data/documents/ (.pdf or .txt). A manifest.json file next
to them gives each file its title and source URL.

Run from the project root:
    python -m app.chunking
"""

import json
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "documents"
MANIFEST_FILE = DOCUMENTS_DIR / "manifest.json"

CHUNK_WORDS = 150
OVERLAP_WORDS = 30
MIN_CHUNK_WORDS = 5  # ignore near-empty pages such as a lone page number


def chunk_text(text, size=CHUNK_WORDS, overlap=OVERLAP_WORDS):
    """Split text into overlapping chunks of about `size` words."""
    if size < 1 or overlap < 0 or overlap >= size:
        raise ValueError("size must be positive and overlap smaller than size")
    words = text.split()
    if len(words) < MIN_CHUNK_WORDS:
        return []

    chunks = []
    step = size - overlap
    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start : start + size]))
        if start + size >= len(words):
            break
    return chunks


def read_pdf_pages(path):
    """Return [(page_number, text)] for every page that has text."""
    reader = PdfReader(str(path))
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = " ".join((page.extract_text() or "").split())
        if text:
            pages.append((number, text))
    return pages


def read_text_sections(path):
    """Return [(section_number, text)] for a .txt file.

    A new section starts at every line that begins with '#'. A file with no
    headings is treated as a single section.
    """
    sections, current = [], []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("#") and current:
            sections.append(" ".join(current))
            current = []
        if line.strip():
            current.append(line.strip())
    if current:
        sections.append(" ".join(current))
    return [(number, text) for number, text in enumerate(sections, start=1)]


def load_manifest(path=MANIFEST_FILE):
    """Read the manifest (file name -> title, source_url, scheme_id)."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Warning: could not read manifest ({error}); using file names.")
        return {}


def build_chunks(
    documents_dir=DOCUMENTS_DIR, size=CHUNK_WORDS, overlap=OVERLAP_WORDS
):
    """Chunk every .pdf and .txt file in documents_dir.

    Each chunk is a dict with: id, text, title, source, page, file, scheme_id.
    """
    documents_dir = Path(documents_dir)
    manifest = load_manifest(documents_dir / "manifest.json")
    chunks = []

    for path in sorted(documents_dir.iterdir()):
        if path.suffix.lower() not in (".pdf", ".txt"):
            continue
        info = manifest.get(path.name, {})
        if not info:
            print(f"Warning: {path.name} is not in manifest.json")

        try:
            if path.suffix.lower() == ".pdf":
                parts = read_pdf_pages(path)
            else:
                parts = read_text_sections(path)
        except (OSError, ValueError, PdfReadError) as error:
            print(f"Skipped {path.name}: {error}")
            continue

        for page, text in parts:
            for index, piece in enumerate(chunk_text(text, size, overlap), start=1):
                chunks.append(
                    {
                        "id": f"{path.stem}-p{page}-c{index}",
                        "text": piece,
                        "title": info.get("title") or path.stem,
                        "source": info.get("source_url") or "unknown",
                        "page": page,
                        "file": path.name,
                        "scheme_id": info.get("scheme_id") or "",
                    }
                )
    return chunks


def main():
    chunks = build_chunks()
    per_file = {}
    for chunk in chunks:
        per_file[chunk["file"]] = per_file.get(chunk["file"], 0) + 1
    for name, count in per_file.items():
        print(f"{name}: {count} chunks")
    print(f"Total: {len(chunks)} chunks")


if __name__ == "__main__":
    main()
