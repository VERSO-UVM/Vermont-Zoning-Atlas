#!/usr/bin/env python3
"""
extract_bylaw_json.py

Extracts the full text of a Vermont municipal zoning bylaw PDF and structures
it as JSON, preserving the complete document hierarchy:

    metadata
    articles
      article  (ARTICLE I / ARTICLE 1 / CHAPTER I / 1. ALL CAPS TITLE)
        sections
          section  (Section 100 / Section 1.1 / 1.1 Title / 100 TITLE)
            paragraphs   (plain text blocks)
            regulations  (dimensional table rows: label + value + unit)
            items        (numbered list items)
            subsections
              subsection  (A. / a) / 1.1.1)
                paragraphs
                items

Handles the main structural formats found across Vermont municipal bylaws:
  - Roman-numeral articles  (ARTICLE I, ARTICLE II)
  - Arabic-number articles  (ARTICLE 1, CHAPTER 1)
  - Keyword-less articles   (1. GENERAL PROVISIONS  -- all caps)
  - Keyword sections        (Section 100, Section 1.1)
  - Decimal sections        (1.1  Title -- no 'Section' keyword)
  - Subsections             (A. Title  /  a) Title  /  1.1.1 Title)

Usage:
    python extract_bylaw_json.py
        (defaults to Addison_Bridport for testing)

    python extract_bylaw_json.py path/to/Town_Bylaw_Text/County_Town_Text_effXXXX.pdf

Output:
    data/Town_Bylaw_Extracted_Data/County_Town.json  (alongside this script)

Requirements:
    pip install pypdf
"""

import re
import sys
import json
from pathlib import Path
from datetime import date

try:
    import pypdf
except ImportError:
    sys.exit("pypdf not installed. Run: pip install pypdf")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
THIS_DIR  = Path(__file__).resolve().parent          # data/Town_Bylaw_Extracted_Data/
REPO_ROOT = THIS_DIR.parent.parent                   # repository root
PDF_DIR   = REPO_ROOT / "data" / "Town_Bylaw_Text"

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Article: "ARTICLE I", "ARTICLE 1:", "CHAPTER IV", "CHAPTER 2 -"
RE_ARTICLE_KW = re.compile(
    r'^(?:ARTICLE|CHAPTER)\s+([IVXLCDM]+|\d+)\s*[:\.\-\u2013]?\s*(.*)',
    re.IGNORECASE
)
# Article (no keyword): "1. ALL CAPS TITLE" -- require all-uppercase text, 8+ chars
RE_ARTICLE_NUM = re.compile(
    r'^(\d{1,2})\.\s+([A-Z][A-Z\s&/()\-]{7,60})$'
)

# Section with keyword: "Section 100", "Section 1.1", "Section 100A"
RE_SECTION_KW = re.compile(
    r'^Section\s+(\d+(?:\.\d+)*[A-Z]?)\s*[:\.]?\s*(.*)',
    re.IGNORECASE
)
# Decimal section without keyword: "1.1  Title" or "1.1. Title"
# Negative lookahead (?!\.\d) avoids matching 1.1.1 (handled as subsection)
RE_SECTION_DECIMAL = re.compile(
    r'^(\d+\.\d+)(?!\.\d)\.?\s{1,4}(.{3,})'
)
# Bare number section: "100  TITLE" or "1005 Title" (3-4 digit code, space(s), title)
RE_SECTION_BARE = re.compile(
    r'^(\d{3,4})\s+(?![\.\d])([A-Z].{3,})'
)
# Numbered-letter subsection: "1005.A  text" (used in Barre City style ordinances)
RE_SUBSECTION_NUM_ALPHA = re.compile(
    r'^(\d{3,4})\.([A-Z])\s+(.{3,})'
)

# Subsection: "A. Title" or "A.  Title"
RE_SUBSECTION_ALPHA = re.compile(r'^([A-Z])\.\s{1,3}(.{3,})')
# Subsection: "a) Title" or "A) Title"
RE_SUBSECTION_PAREN = re.compile(r'^([a-zA-Z])\)\s+(.{3,})')
# Subsection (decimal third-level): "1.1.1  Title"
RE_SUBSECTION_DECIMAL = re.compile(r'^(\d+\.\d+\.\d+)\.?\s{1,4}(.{3,})')

# Numbered list item: "1. text"
RE_LIST_ITEM = re.compile(r'^(\d+)\.\s+(.+)')

# Use-type list headers
RE_USE_HEADER = re.compile(
    r'^(By[\s\-]?Right Uses?|Permitted Uses?|Conditional Uses?|Prohibited Uses?|Allowed Uses?)\s*:?\s*$',
    re.IGNORECASE
)

# Dimensional regulation rows: "Label     value  unit"
RE_REGULATION = re.compile(
    r'^([A-Za-z][A-Za-z ,/\-]{4,55}?)\s{3,}(\d+(?:\.\d+)?)'
    r'\s*(acres?|feet|ft\.?|percent|%|stories|units?|spaces?|'
    r'square\s*feet|sq\.?\s*ft\.?|inches?|miles?|days?)?\s*$',
    re.IGNORECASE
)

# Short repeated page headers / footers / page numbers to discard
RE_PAGE_ARTIFACT = re.compile(
    r'^(zoning regulations?|land use.*regulations?|unified development'
    r'|town of \w[\w\s]{0,25}|vermont|\d{1,3}|page \d+|\|[\s\d]+\|)$',
    re.IGNORECASE
)

# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------
CHAR_MAP = {
    '\ufffd': "'", '\u2019': "'", '\u2018': "'",
    '\u201c': '"', '\u201d': '"',
    '\u2013': '-', '\u2014': '--',
    '\u00e9': 'e', '\u00e8': 'e', '\u00ea': 'e',
    '\u00e0': 'a', '\u00e2': 'a',
    '\u00b7': '*', '\u2022': '*', '\uf0b7': '*',  # bullet variants
    '\u00a7': 'S',  # section sign
    '\u00ae': '(R)', '\u2122': '(TM)',
}


def clean(text):
    for bad, good in CHAR_MAP.items():
        text = text.replace(bad, good)
    # collapse whitespace, strip control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def is_toc_line(line):
    """Table of Contents lines have dotted leaders: '.........'"""
    return bool(re.search(r'\.{4,}', line))


def is_page_artifact(line):
    """Short repeated page headers/footers/numbers."""
    return bool(RE_PAGE_ARTIFACT.match(line)) and len(line) < 80


# ---------------------------------------------------------------------------
# PDF extraction
# ---------------------------------------------------------------------------
def extract_pages(pdf_path):
    reader = pypdf.PdfReader(str(pdf_path))
    pages = []
    for i, page in enumerate(reader.pages, 1):
        text = clean(page.extract_text() or '')
        pages.append((i, text))
    return pages, len(reader.pages)


def pages_to_lines(pages):
    """Flatten pages into (page_num, line) pairs, stripping TOC and artifacts."""
    lines = []
    for page_num, text in pages:
        for raw in text.split('\n'):
            line = clean(raw)
            if not line:
                continue
            if is_toc_line(line):
                continue
            if is_page_artifact(line):
                continue
            lines.append((page_num, line))
    return lines


# ---------------------------------------------------------------------------
# Pattern matchers
# ---------------------------------------------------------------------------
def match_article(line):
    """Return (number, title) if line is an article/chapter header, else None."""
    m = RE_ARTICLE_KW.match(line)
    if m:
        num = m.group(1).upper()
        # Sanity check: arabic article numbers > 25 are almost certainly false positives
        if num.isdigit() and int(num) > 25:
            return None
        return num, re.sub(r'\.+\s*$', '', m.group(2)).strip()
    m = RE_ARTICLE_NUM.match(line)
    if m:
        return m.group(1), re.sub(r'\.+\s*$', '', m.group(2)).strip()
    return None


def match_section(line):
    """Return (number, title) if line is a section header, else None."""
    m = RE_SECTION_KW.match(line)
    if m:
        return m.group(1).upper(), re.sub(r'\.+\s*$', '', m.group(2)).strip()
    m = RE_SECTION_DECIMAL.match(line)
    if m:
        return m.group(1), re.sub(r'\.+\s*$', '', m.group(2)).strip()
    m = RE_SECTION_BARE.match(line)
    if m:
        return m.group(1), re.sub(r'\.+\s*$', '', m.group(2)).strip()
    return None


def match_subsection(line):
    """Return (label, title) if line is a subsection header, else None."""
    m = RE_SUBSECTION_DECIMAL.match(line)
    if m and len(line) < 150:
        return m.group(1), re.sub(r'\.+\s*$', '', m.group(2)).strip()
    m = RE_SUBSECTION_NUM_ALPHA.match(line)
    if m:
        return f'{m.group(1)}.{m.group(2)}', m.group(3).strip()
    m = RE_SUBSECTION_ALPHA.match(line)
    if m and len(line) < 120:
        return m.group(1).upper(), re.sub(r'\.+\s*$', '', m.group(2)).strip()
    m = RE_SUBSECTION_PAREN.match(line)
    if m and len(line) < 120:
        return m.group(1).upper(), re.sub(r'\.+\s*$', '', m.group(2)).strip()
    return None


# ---------------------------------------------------------------------------
# Document parser
# ---------------------------------------------------------------------------
def parse_document(lines):
    """
    Walk lines and build:
        {articles: [{number, title, sections: [{number, title, page,
            paragraphs, subsections: [{label, title, paragraphs, items:[]}],
            regulations:[{label,value,unit}], items:[]}]}]}
    """
    doc = {'articles': []}
    current_art         = None
    current_sec         = None
    current_sub         = None
    current_use_type    = None
    pending_lines       = []
    committed_articles  = set()  # numbers of articles that already have ≥1 section

    def flush(target, buf):
        if buf and target is not None:
            text = ' '.join(buf).strip()
            if text:
                target.setdefault('paragraphs', []).append(text)
        return []

    def current_text_target():
        if current_sub is not None:
            return current_sub
        if current_sec is not None:
            return current_sec
        return None

    def ensure_article():
        """Create an implicit article if none has been seen yet."""
        nonlocal current_art
        if current_art is None:
            current_art = {'number': '', 'title': '', 'sections': []}
            doc['articles'].append(current_art)

    for page_num, line in lines:

        # ── Article header ────────────────────────────────────────────────────
        art = match_article(line)
        if art:
            number, title = art
            # Skip repeated headers of already-committed articles (page header repetition)
            if number != '' and number in committed_articles:
                continue
            pending_lines = flush(current_text_target(), pending_lines)
            # Reuse an empty placeholder created from the TOC (no sections yet)
            existing = next(
                (a for a in doc['articles'] if a['number'] == number and not a['sections']),
                None
            )
            if existing:
                existing['title'] = title   # real header may be fuller than TOC entry
                current_art = existing
            else:
                current_art = {'number': number, 'title': title, 'sections': []}
                doc['articles'].append(current_art)
            current_sec = None
            current_sub = None
            current_use_type = None
            continue

        # ── Deep subsections (1.1.1 / 1005.A) — check before section to avoid overlap ─
        # Only try these patterns when already inside a section
        if current_sec is not None:
            m_sub_decimal = RE_SUBSECTION_DECIMAL.match(line)
            m_sub_numalpha = RE_SUBSECTION_NUM_ALPHA.match(line)
            if (m_sub_decimal and len(line) < 150) or m_sub_numalpha:
                pending_lines = flush(current_text_target(), pending_lines)
                if m_sub_decimal:
                    label = m_sub_decimal.group(1)
                    title = re.sub(r'\.+\s*$', '', m_sub_decimal.group(2)).strip()
                else:
                    label = f'{m_sub_numalpha.group(1)}.{m_sub_numalpha.group(2)}'
                    title = m_sub_numalpha.group(3).strip()
                current_sub = {'label': label, 'title': title, 'paragraphs': [], 'items': []}
                current_sec['subsections'].append(current_sub)
                current_use_type = None
                continue

        # ── Section header ────────────────────────────────────────────────────
        sec = match_section(line)
        if sec and len(line) < 160:
            pending_lines = flush(current_text_target(), pending_lines)
            ensure_article()
            number, title = sec
            current_sec = {
                'number': number,
                'title': title,
                'page': page_num,
                'paragraphs': [],
                'subsections': [],
                'regulations': [],
                'items': [],
            }
            current_art['sections'].append(current_sec)
            committed_articles.add(current_art['number'])
            current_sub = None
            current_use_type = None
            continue

        if current_sec is None:
            continue

        # ── Subsection header (A. / a) ) ──────────────────────────────────────
        m = RE_SUBSECTION_ALPHA.match(line)
        if not m:
            m = RE_SUBSECTION_PAREN.match(line)
        if m and len(line) < 120:
            pending_lines = flush(current_text_target(), pending_lines)
            label = m.group(1).upper()
            title = re.sub(r'\.+\s*$', '', m.group(2)).strip()
            current_sub = {'label': label, 'title': title, 'paragraphs': [], 'items': []}
            current_sec['subsections'].append(current_sub)
            current_use_type = None
            continue

        # ── Use-list header ───────────────────────────────────────────────────
        m = RE_USE_HEADER.match(line)
        if m:
            pending_lines = flush(current_text_target(), pending_lines)
            raw = m.group(1).lower()
            if 'right' in raw or 'permitted' in raw or 'allowed' in raw:
                current_use_type = 'by_right'
            elif 'conditional' in raw:
                current_use_type = 'conditional'
            elif 'prohibit' in raw:
                current_use_type = 'prohibited'
            else:
                current_use_type = 'other'
            pending_lines.append(line)
            continue

        # ── Numbered list item ────────────────────────────────────────────────
        m = RE_LIST_ITEM.match(line)
        if m:
            pending_lines = flush(current_text_target(), pending_lines)
            item = {
                'number': m.group(1),
                'text': m.group(2).strip(),
                'use_type': current_use_type,
            }
            target = current_sub if current_sub is not None else current_sec
            target.setdefault('items', []).append(item)
            continue

        # ── Regulation table row ──────────────────────────────────────────────
        m = RE_REGULATION.match(line)
        if m:
            pending_lines = flush(current_text_target(), pending_lines)
            reg = {
                'label': m.group(1).strip(),
                'value': m.group(2),
                'unit':  (m.group(3) or '').strip().lower(),
            }
            current_sec.setdefault('regulations', []).append(reg)
            continue

        # ── Plain text ────────────────────────────────────────────────────────
        pending_lines.append(line)

    flush(current_text_target(), pending_lines)
    return doc


# ---------------------------------------------------------------------------
# Filename helpers
# ---------------------------------------------------------------------------
def output_name_from_pdf(pdf_path):
    """'Addison_Bridport_Text_eff08222006.pdf'  ->  'Addison_Bridport'"""
    stem = Path(pdf_path).stem
    parts = stem.split('_')
    skip = {'text', 'bylaw', 'zoning', 'regulations', 'floodhazard', 'map'}
    kept = []
    for p in parts:
        if p.lower() in skip:
            break
        if re.match(r'^eff\d+', p, re.I):
            break
        kept.append(p)
    return '_'.join(kept[:2]) if len(kept) >= 2 else kept[0]


def bylaw_date_from_filename(pdf_path):
    m = re.search(r'eff(\d{4,8})', Path(pdf_path).stem, re.I)
    if not m:
        return 'unknown'
    d = m.group(1)
    if len(d) == 8:
        return f'{d[:4]}-{d[4:6]}-{d[6:]}'
    if len(d) == 6:
        return f'{d[:2]}/{d[2:4]}/{d[4:]}'
    return d


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(pdf_path=None):
    if pdf_path is None:
        pdf_path = PDF_DIR / 'Addison_Bridport_Text_eff08222006.pdf'
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        sys.exit(f'ERROR: File not found: {pdf_path}')

    print(f'Extracting: {pdf_path.name}')

    pages, num_pages = extract_pages(pdf_path)
    lines = pages_to_lines(pages)
    total_words = sum(len(l.split()) for _, l in lines)
    print(f'  Pages: {num_pages}  |  Lines: {len(lines):,}  |  Words: {total_words:,}')

    doc = parse_document(lines)
    num_arts  = len(doc['articles'])
    num_secs  = sum(len(a['sections']) for a in doc['articles'])
    num_subs  = sum(len(s['subsections']) for a in doc['articles'] for s in a['sections'])
    num_regs  = sum(len(s['regulations']) for a in doc['articles'] for s in a['sections'])
    num_items = sum(
        len(s.get('items', [])) +
        sum(len(sub.get('items', [])) for sub in s['subsections'])
        for a in doc['articles'] for s in a['sections']
    )
    print(f'  Parsed: {num_arts} articles  |  {num_secs} sections  |  {num_subs} subsections')
    print(f'           {num_regs} regulation rows  |  {num_items} list items')

    out_name   = output_name_from_pdf(pdf_path)
    name_parts = out_name.split('_')
    county     = name_parts[0] if name_parts else 'Unknown'
    muni       = name_parts[1] if len(name_parts) > 1 else name_parts[0]

    output = {
        'metadata': {
            'municipality':      muni,
            'county':            county,
            'state':             'Vermont',
            'bylaw_date':        bylaw_date_from_filename(pdf_path),
            'source_pdf':        pdf_path.name,
            'extracted_date':    str(date.today()),
            'pages':             num_pages,
            'word_count':        total_words,
            'articles_found':    num_arts,
            'sections_found':    num_secs,
            'subsections_found': num_subs,
            'regulation_rows':   num_regs,
            'list_items':        num_items,
        },
        'articles': doc['articles'],
    }

    out_path = THIS_DIR / f'{out_name}.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    size_kb = out_path.stat().st_size // 1024
    print(f'  Written: {out_path.name}  ({size_kb} KB)')
    print('Done.')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)
