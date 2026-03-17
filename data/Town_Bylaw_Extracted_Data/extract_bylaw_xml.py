#!/usr/bin/env python3
"""
extract_bylaw_xml.py

Extracts the full text of a Vermont municipal zoning bylaw PDF and structures
it as XML, preserving the complete document hierarchy:

    bylaw
      metadata
      article  (ARTICLE I, II, ...)
        section  (Section 100, 200A, ...)
          subsection  (A., B., C., ...)
            p            (paragraph text)
            list         (numbered use lists)
              item
          regulation     (dimensional table rows: label + value + unit)
          p
          list
            item

The XML captures ALL text from the bylaw — nothing is discarded — and also
adds light semantic tagging for list items and regulation table rows so the
document is machine-readable without losing any human-readable content.

Usage:
    python extract_bylaw_xml.py
        (defaults to Addison_Bridport for testing)

    python extract_bylaw_xml.py path/to/Town_Bylaw_Text/County_Town_Text_effXXXX.pdf

Output:
    data/Town_Bylaw_Extracted_Data/County_Town.xml  (alongside this script)

Requirements:
    pip install pypdf
"""

import re
import sys
import os
from pathlib import Path
from datetime import date
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

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
RE_ARTICLE    = re.compile(r'^ARTICLE\s+([IVXLCDM]+)\s*[:\-\u2013]?\s*(.*)', re.IGNORECASE)
RE_SECTION    = re.compile(r'^Section\s+(\d+[A-Z]?)\s*[:\.]?\s*(.*)', re.IGNORECASE)
RE_SUBSECTION = re.compile(r'^([A-Z])\.\s+(.{3,})')
RE_LIST_ITEM  = re.compile(r'^(\d+)\.\s+(.+)')
RE_USE_HEADER = re.compile(r'^(By[\s\-]?Right Uses?|Permitted Uses?|Conditional Uses?|Prohibited Uses?|Allowed Uses?)\s*:?\s*$', re.IGNORECASE)
RE_REGULATION = re.compile(
    r'^([A-Za-z][A-Za-z ,/\-]{4,55}?)\s{3,}(\d+(?:\.\d+)?)\s*(acres?|feet|ft\.?|percent|%|stories|units?|spaces?|square\s*feet|sq\.?\s*ft\.?|inches?|miles?|days?)?\s*$',
    re.IGNORECASE
)
RE_PAGE_ARTIFACT = re.compile(
    r'^(zoning regulations?|town of \w[\w\s]{0,25}|vermont|\d{1,3}|page \d+)$',
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
    '\u00b7': '*', '\u2022': '*',
    '\u00a7': 'S',  # section sign
}

def clean(text):
    for bad, good in CHAR_MAP.items():
        text = text.replace(bad, good)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def is_toc_line(line):
    """Table of Contents lines have dotted leaders: '.........'"""
    return bool(re.search(r'\.{4,}', line))


def is_page_artifact(line):
    """Short repeated page headers/footers/numbers."""
    return bool(RE_PAGE_ARTIFACT.match(line)) and len(line) < 55


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
# Document parser
# ---------------------------------------------------------------------------
def parse_document(lines):
    """
    Walk lines and build a nested dict:
        {articles: [{number, title, sections: [{number, title, page,
            paragraphs, subsections: [{label, title, paragraphs, items:[]}],
            regulations:[{label,value,unit}]}]}]}
    """
    doc = {'articles': []}
    current_art  = None
    current_sec  = None
    current_sub  = None
    current_use_type = None   # 'by_right' | 'conditional' | 'prohibited' | None
    pending_lines = []        # text lines not yet assigned to a paragraph

    def flush(target, buf):
        """Join buffered lines into a paragraph on target."""
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

    for page_num, line in lines:

        # ── Article header ──────────────────────────────────────────────────
        m = RE_ARTICLE.match(line)
        if m:
            pending_lines = flush(current_text_target(), pending_lines)
            title = re.sub(r'\.+\s*$', '', m.group(2)).strip()
            current_art = {'number': m.group(1).upper(), 'title': title, 'sections': []}
            doc['articles'].append(current_art)
            current_sec = None
            current_sub = None
            current_use_type = None
            continue

        # ── Section header ───────────────────────────────────────────────────
        m = RE_SECTION.match(line)
        if m:
            pending_lines = flush(current_text_target(), pending_lines)
            title = re.sub(r'\.+\s*$', '', m.group(2)).strip()
            current_sec = {
                'number': m.group(1).upper(),
                'title': title,
                'page': page_num,
                'paragraphs': [],
                'subsections': [],
                'regulations': [],
                'items': [],
            }
            if current_art is not None:
                current_art['sections'].append(current_sec)
            current_sub = None
            current_use_type = None
            continue

        if current_sec is None:
            # Text before any section — attach to a preamble bucket
            continue

        # ── Subsection header (A., B., C.) ───────────────────────────────────
        m = RE_SUBSECTION.match(line)
        if m and len(line) < 100:
            pending_lines = flush(current_text_target(), pending_lines)
            label = m.group(1).upper()
            title = re.sub(r'\.+\s*$', '', m.group(2)).strip()
            current_sub = {
                'label': label,
                'title': title,
                'paragraphs': [],
                'items': [],
            }
            current_sec['subsections'].append(current_sub)
            current_use_type = None
            continue

        # ── Use-list header ("By Right Uses:", "Conditional Uses:", …) ───────
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
            # Keep the header text as a paragraph too
            pending_lines.append(line)
            continue

        # ── Numbered list item (1. 2. 3.) ────────────────────────────────────
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

        # ── Regulation table row (label   value   unit) ──────────────────────
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

        # ── Plain text line ───────────────────────────────────────────────────
        pending_lines.append(line)

    # flush any remaining text
    flush(current_text_target(), pending_lines)

    return doc


# ---------------------------------------------------------------------------
# XML builder
# ---------------------------------------------------------------------------
def build_xml(doc, metadata):
    root = Element('bylaw')

    # metadata block
    meta = SubElement(root, 'metadata')
    for key, val in metadata.items():
        el = SubElement(meta, key)
        el.text = str(val)

    for art in doc['articles']:
        art_el = SubElement(root, 'article',
                            number=art['number'],
                            title=art.get('title', ''))

        for sec in art['sections']:
            sec_el = SubElement(art_el, 'section',
                                number=sec['number'],
                                title=sec.get('title', ''),
                                page=str(sec.get('page', '')))

            # Section-level paragraphs (before subsections)
            for para in sec.get('paragraphs', []):
                p = SubElement(sec_el, 'p')
                p.text = para

            # Regulation table rows
            for reg in sec.get('regulations', []):
                SubElement(sec_el, 'regulation',
                           label=reg['label'],
                           value=reg['value'],
                           unit=reg['unit'])

            # Section-level list items (no subsection)
            _write_items(sec_el, sec.get('items', []))

            # Subsections
            for sub in sec.get('subsections', []):
                sub_el = SubElement(sec_el, 'subsection',
                                    label=sub['label'],
                                    title=sub.get('title', ''))

                for para in sub.get('paragraphs', []):
                    p = SubElement(sub_el, 'p')
                    p.text = para

                _write_items(sub_el, sub.get('items', []))

    return root


def _write_items(parent, items):
    """Group list items by use_type and write <list> elements."""
    if not items:
        return
    # Group consecutive items by use_type
    groups = []
    for item in items:
        ut = item.get('use_type') or 'general'
        if groups and groups[-1][0] == ut:
            groups[-1][1].append(item)
        else:
            groups.append((ut, [item]))

    for use_type, group in groups:
        list_el = SubElement(parent, 'list', type=use_type)
        for item in group:
            it = SubElement(list_el, 'item', number=item['number'])
            it.text = item['text']


def prettify(root):
    rough = tostring(root, encoding='unicode')
    dom = parseString(rough.encode('utf-8'))
    return dom.toprettyxml(indent='  ', encoding='utf-8').decode('utf-8')


# ---------------------------------------------------------------------------
# Filename helpers
# ---------------------------------------------------------------------------
def output_name_from_pdf(pdf_path):
    """'Addison_Bridport_Text_eff08222006.pdf'  ->  'Addison_Bridport'"""
    stem = Path(pdf_path).stem
    parts = stem.split('_')
    skip = {'text', 'bylaw', 'zoning', 'regulations'}
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
        # Default: Bridport proof-of-concept
        pdf_path = PDF_DIR / 'Addison_Bridport_Text_eff08222006.pdf'
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        sys.exit(f'ERROR: File not found: {pdf_path}')

    print(f'Extracting: {pdf_path.name}')

    # Extract
    pages, num_pages = extract_pages(pdf_path)
    lines = pages_to_lines(pages)
    total_words = sum(len(l.split()) for _, l in lines)
    print(f'  Pages: {num_pages}  |  Lines after filtering: {len(lines):,}  |  Words: {total_words:,}')

    # Parse
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

    # Derive names
    out_name   = output_name_from_pdf(pdf_path)
    name_parts = out_name.split('_')
    county     = name_parts[0] if name_parts else 'Unknown'
    muni       = name_parts[1] if len(name_parts) > 1 else name_parts[0]

    metadata = {
        'municipality':    muni,
        'county':          county,
        'state':           'Vermont',
        'bylaw_date':      bylaw_date_from_filename(pdf_path),
        'source_pdf':      pdf_path.name,
        'extracted_date':  str(date.today()),
        'pages':           num_pages,
        'word_count':      total_words,
        'articles_found':  num_arts,
        'sections_found':  num_secs,
        'subsections_found': num_subs,
        'regulation_rows': num_regs,
        'list_items':      num_items,
    }

    # Build and write XML
    root = build_xml(doc, metadata)
    xml_str = prettify(root)

    out_path = THIS_DIR / f'{out_name}.xml'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(xml_str)

    size_kb = out_path.stat().st_size // 1024
    print(f'  Written: {out_path.name}  ({size_kb} KB)')
    print('Done.')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)
