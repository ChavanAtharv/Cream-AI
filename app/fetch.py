"""Download source documents for SchemeSaathi.

Run from the project root:
    python -m app.fetch
"""

from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "documents"

TIMEOUT_SECONDS = 15
HEADERS = {"User-Agent": "SchemeSaathi/0.1 (student project)"}

# name -> official URL. Replace or extend these with official guideline PDFs
# from ministry websites; later days chunk these files for search.
DOCUMENTS = {
    "pm_kisan_myscheme": "https://www.myscheme.gov.in/schemes/pm-kisan",
    "pmjjby_myscheme": "https://www.myscheme.gov.in/schemes/pmjjby",
    "dpiit_internship_myscheme": "https://www.myscheme.gov.in/schemes/dpiit-is",
}

CONTENT_TYPE_EXTENSIONS = {
    "application/pdf": ".pdf",
    "text/html": ".html",
    "application/json": ".json",
    "text/plain": ".txt",
}


class FetchError(Exception):
    """Raised when a document cannot be downloaded or saved."""


def extension_for(content_type):
    """Pick a file extension from a Content-Type header value."""
    mime = (content_type or "").split(";")[0].strip().lower()
    return CONTENT_TYPE_EXTENSIONS.get(mime, ".bin")


def fetch_document(name, url, dest_dir=DOCUMENTS_DIR, timeout=TIMEOUT_SECONDS):
    """Download one document and return the saved file path.

    Raises FetchError with a readable message on any failure.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.Timeout as error:
        raise FetchError(f"timed out after {timeout}s") from error
    except requests.exceptions.HTTPError as error:
        raise FetchError(f"HTTP error: {error}") from error
    except requests.exceptions.RequestException as error:
        raise FetchError(f"request failed: {error}") from error

    if not response.content:
        raise FetchError("empty response")

    extension = extension_for(response.headers.get("Content-Type"))
    path = Path(dest_dir) / f"{name}{extension}"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(response.content)
    except OSError as error:
        raise FetchError(f"could not save file: {error}") from error
    return path


def download_all(documents=None, dest_dir=DOCUMENTS_DIR):
    """Download every document, continuing past failures.

    Returns (saved, failed): saved maps name -> path, failed maps name -> reason.
    """
    documents = DOCUMENTS if documents is None else documents
    saved, failed = {}, {}
    for name, url in documents.items():
        try:
            saved[name] = fetch_document(name, url, dest_dir=dest_dir)
            print(f"Saved {name}: {saved[name]}")
        except FetchError as error:
            failed[name] = str(error)
            print(f"Failed {name}: {error}")
    return saved, failed


def main():
    saved, failed = download_all()
    print(f"\nDownloaded {len(saved)} of {len(saved) + len(failed)} documents.")


if __name__ == "__main__":
    main()