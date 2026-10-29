#!/usr/bin/env python3
"""
convert_to_vcgi_schema.py

Aligns zoning GeoJSONs with the Vermont Zoning GIS Data Standard v2.0
(https://files.vcgi.vermont.gov/other/standards-guidelines/zoning/zoning-standard.html)
for every field that has a VCGI equivalent:

  1. Renames matching fields to their VCGI names, keeping property order.
  2. Our 4+ unit fields (F4F_*) feed both VCGI's 4-unit and 5+ unit fields,
     since a 4+ unit rule applies to both.
  3. Converts RPC values to VCGI 2-character codes.
  4. Converts treatment values to VCGI codes where the meaning is unambiguous
     (Permitted -> AP, Public Hearing -> CU, Prohibited -> PR). Values with no
     clear VCGI code (Allowed/Conditional, Not Mentioned, Overlay) are kept
     and reported.

Only the changed keys and values are rewritten; geometry and every other
value keep their exact original text. Already-converted files are left
unchanged, so the script is safe to re-run.

For newly collected data, run normalize_properties.py first (raw RPC fields ->
our field names), then this script, then enforce_canonical_fields.py.

Usage:
    python scripts/convert_to_vcgi_schema.py
"""

import collections
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

TARGETS = [
    REPO_ROOT / "data" / "State_of_Vermont",
    REPO_ROOT / "data" / "RPC",
    REPO_ROOT / "data" / "Vermont_Statewide.geojson",
    REPO_ROOT / "data_summer_2026",
    REPO_ROOT / "Fall25Spring26Data",
]

# Old field -> VCGI field(s). A second name is inserted right after the first.
FIELD_RENAMES = {
    "County":                               ["COUNTY"],
    "Municipal_Name":                       ["JXTN"],
    "GEO_ID":                               ["GEOID"],
    "District_Name":                        ["DIST_NAME"],
    "Abbreviated_District_Name":            ["ABBRDISTNM"],
    "Overlay_District":                     ["OVER"],
    "F1F_Allowance":                        ["UT1"],
    "F2F_Allowance":                        ["UT2"],
    "F3F_Allowance":                        ["UT3"],
    "F4F_Allowance":                        ["UT4", "UT5"],
    "F1F_Min_Lot_Size":                     ["MIN_LOT_1U"],
    "F2F_Min_Lot_Size":                     ["MIN_LOT_2U"],
    "F3F_Min_Lot_Size":                     ["MIN_LOT_3U"],
    "F4F_Min_Lot_Size":                     ["MIN_LOT_4U", "MIN_LOT_5U"],
    "F2F_Max_Density":                      ["MAX_DEN_2U"],
    "F3F_Max_Density":                      ["MAX_DEN_3U"],
    "F4F_Max_Density":                      ["MAX_DEN_4U", "MAX_DEN_5U"],
    "ADU_Allowance":                        ["ADUDP"],
    "PRD_Allowance":                        ["PRDDP"],
    "PRD_Mobile_or_Manufactured_Home_Park": ["PRD_MHP"],
    "Notes":                                ["NOTE"],
}

RPC_CODES = {
    "ACRPC": "AC",
    "BCRC":  "BC",
    "CVRPC": "CV",
    "CCRPC": "CC",
    "LCPC":  "LC",
    "NVDA":  "NV",
    "NRPC":  "NW",
    "NWRPC": "NW",
    "RRPC":  "RR",
    "MARC":  "MA",
    "TRORC": "TR",
    "WRC":   "WR",
}

TREATMENT_FIELDS = ["UT1", "UT2", "UT3", "UT4", "UT5", "ADUDP", "PRDDP"]

TREATMENT_CODES = {
    "permitted":      "AP",
    "public hearing": "CU",
    "prohibited":     "PR",
    "prohibiited":    "PR",  # typo present in source data
}

CONTROL_CHARS = re.compile(r"[\x00-\x1f]")
DECODER = json.JSONDecoder()


def clean(value):
    """Strip whitespace and stray control characters (e.g. \\x08) from a string."""
    return CONTROL_CHARS.sub("", value).strip()


def convert_value(key, value, unmapped):
    """Return the VCGI form of a single value (after renaming)."""
    if key == "RPC" and isinstance(value, str):
        return RPC_CODES.get(value.strip(), value)

    if key in TREATMENT_FIELDS and isinstance(value, str):
        value = clean(value)
        code = TREATMENT_CODES.get(value.lower())
        if code:
            return code
        unmapped[(key, value)] += 1

    return value


def convert_props_text(span, unmapped):
    """
    Convert one serialized properties object. Works on the raw text so that
    untouched keys and values (and their number formatting) are kept verbatim.
    """
    pairs = []      # (key, sep_text, value_text, value) in original order
    joiners = []    # text between consecutive pairs, e.g. "," or ", "
    tail = span[1:] # text after the last value, through the closing brace
    i = 1
    while True:
        while span[i] in " \n\t\r":
            i += 1
        if span[i] == "}":
            break
        key, end = DECODER.raw_decode(span, i)
        colon = span.index(":", end) + 1
        while span[colon] == " ":
            colon += 1
        value, vend = DECODER.raw_decode(span, colon)
        pairs.append((key, span[end:colon], span[colon:vend], value))
        tail = span[vend:]
        nxt = vend
        while span[nxt] in " \n\t\r":
            nxt += 1
        if span[nxt] == ",":
            j = nxt + 1
            while span[j] in " \n\t\r":
                j += 1
            joiners.append(span[vend:j])
            i = j
        else:
            i = nxt

    ensure_ascii = "\\u" in span
    joiner = joiners[0] if joiners else ","
    out = []
    for key, sep, raw_value, value in pairs:
        for new_key in FIELD_RENAMES.get(key, [key]):
            new_value = convert_value(new_key, value, unmapped)
            if new_value != value:
                raw_value = json.dumps(new_value, ensure_ascii=ensure_ascii)
            out.append(json.dumps(new_key, ensure_ascii=ensure_ascii) + sep + raw_value)

    return "{" + joiner.join(out) + tail


def convert_file(fpath, unmapped):
    """Convert one GeoJSON in place. Returns number of features changed."""
    text = fpath.read_text(encoding="utf-8")
    pieces = []
    pos = 0
    changed = 0
    while True:
        i = text.find('"properties"', pos)
        if i < 0:
            break
        start = text.index(":", i) + 1
        while text[start] == " ":
            start += 1
        if text[start] != "{":
            pos = start
            continue
        _, end = DECODER.raw_decode(text, start)
        span = text[start:end]
        new_span = convert_props_text(span, unmapped)
        if new_span != span:
            changed += 1
        pieces.append(text[pos:start])
        pieces.append(new_span)
        pos = end
    pieces.append(text[pos:])

    if changed:
        fpath.write_text("".join(pieces), encoding="utf-8")
    return changed


def main():
    files = []
    for target in TARGETS:
        files.extend(sorted(target.glob("*.geojson")) if target.is_dir() else [target])

    unmapped = collections.Counter()
    touched = 0
    for fpath in files:
        changed = convert_file(fpath, unmapped)
        if changed:
            touched += 1
            print(f"  {fpath.relative_to(REPO_ROOT)}: {changed} features")

    print(f"\nFiles converted: {touched} / {len(files)}")

    if unmapped:
        print("\nTreatment values with no VCGI code (left as-is):")
        for (field, value), n in sorted(unmapped.items()):
            print(f"  {field:<6} {value!r}: {n}")

    print("\nDone.")


if __name__ == "__main__":
    main()
