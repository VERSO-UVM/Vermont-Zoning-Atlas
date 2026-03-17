"""
Extract text from Vermont zoning bylaw PDFs and save to a single JSON file.
Filename format: {County}_{Town}_Text_eff{MMDDYYYY}.pdf

Uses pypdf for lightweight text extraction (no page rendering).
Large scanned-image PDFs will return empty text gracefully.
"""

import json
import re
import signal
import sys
from pathlib import Path

import pypdf


DATA_DIR = Path(__file__).parent.parent / "data" / "zoning_bylaws"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "zoning_bylaws_vermont.json"
TIMEOUT_SECONDS = 60  # per file


# ---------------------------------------------------------------------------
# Filename parsing
# ---------------------------------------------------------------------------

def parse_filename(filename: str) -> dict:
    """Extract county, town, and effective date from filename."""
    stem = Path(filename).stem  # strip extension
    # Pattern: County_Town_Text_eff{date}
    match = re.match(r"^(.+?)_(.+?)_Text_eff(\d+)", stem, re.IGNORECASE)
    if not match:
        return {"county": None, "town": None, "effective_date": None}

    county = match.group(1).replace("-", " ").strip()
    town = match.group(2).replace("-", " ").strip()
    raw_date = match.group(3)

    return {"county": county, "town": town, "effective_date": parse_date(raw_date)}


def parse_date(raw: str) -> str:
    """Normalize raw date string to YYYY-MM-DD (or YYYY-MM where day unknown)."""
    raw = raw.strip()
    if len(raw) == 8:   # MMDDYYYY
        return f"{raw[4:]}-{raw[:2]}-{raw[2:4]}"
    elif len(raw) == 6:  # MMYYYY
        return f"{raw[2:]}-{raw[:2]}"
    elif len(raw) == 7:  # MDDYYYY (single-digit month)
        return f"{raw[3:]}-{raw[:1].zfill(2)}-{raw[1:3]}"
    return raw  # unknown format — keep as-is


# ---------------------------------------------------------------------------
# Text extraction with timeout
# ---------------------------------------------------------------------------

class TimeoutError(Exception):
    pass


def _timeout_handler(signum, frame):
    raise TimeoutError("Timed out")


def extract_text(pdf_path: Path) -> tuple[str, str | None]:
    """
    Extract embedded text from a PDF using pypdf.
    Returns (text, error). Scanned-image PDFs return ("", None).
    Times out after TIMEOUT_SECONDS.
    """
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(TIMEOUT_SECONDS)
    try:
        pages = []
        reader = pypdf.PdfReader(str(pdf_path))
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                pages.append(text)
        signal.alarm(0)
        return "\n\n".join(pages), None
    except TimeoutError:
        return "", f"Timed out after {TIMEOUT_SECONDS}s"
    except Exception as e:
        signal.alarm(0)
        return "", str(e)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    pdf_files = sorted(DATA_DIR.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files in {DATA_DIR}\n")

    records = []
    errors = []

    for i, pdf_path in enumerate(pdf_files, 1):
        size_mb = pdf_path.stat().st_size / 1_048_576
        print(f"[{i:3}/{len(pdf_files)}] {pdf_path.name}  ({size_mb:.1f} MB)", end="  ", flush=True)

        metadata = parse_filename(pdf_path.name)
        text, error = extract_text(pdf_path)

        record = {
            "filename": pdf_path.name,
            "county": metadata["county"],
            "town": metadata["town"],
            "effective_date": metadata["effective_date"],
            "text": text,
        }
        if error:
            record["extraction_error"] = error
            errors.append(pdf_path.name)
            print(f"ERROR: {error}")
        else:
            word_count = len(text.split())
            status = f"{word_count:,} words" if word_count else "no embedded text (likely scanned)"
            print(status)

        records.append(record)

    # Report skipped non-PDF files
    non_pdf = [f.name for f in DATA_DIR.iterdir() if f.suffix.lower() != ".pdf"]
    if non_pdf:
        print(f"\nSkipped non-PDF files: {non_pdf}")

    output = {
        "source": "Vermont Zoning Bylaws",
        "total_documents": len(records),
        "documents": records,
    }

    OUTPUT_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nDone. Saved {len(records)} records -> {OUTPUT_FILE}")
    if errors:
        print(f"Files with errors: {errors}")


if __name__ == "__main__":
    main()
