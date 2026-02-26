#!/usr/bin/env python3
"""
enforce_canonical_fields.py

For every GeoJSON in data/State_of_Vermont/:
  1. Adds any canonical fields missing from each feature (set to null).
  2. Reorders each feature's properties to match the canonical field order
     defined in analysis/canonical_fields.csv.
  3. Any fields present in the file but NOT in canonical_fields.csv are
     preserved at the end (they are logged as warnings).

After running, rebuilds data/Vermont_Statewide.geojson.

Usage:
    python scripts/enforce_canonical_fields.py
"""

import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOV_DIR   = REPO_ROOT / "data" / "State_of_Vermont"
CSV_PATH  = REPO_ROOT / "analysis" / "canonical_fields.csv"
OUT_PATH  = REPO_ROOT / "data" / "Vermont_Statewide.geojson"


def load_canonical_fields():
    """Return ordered list of canonical field names (deduplicated, preserving first occurrence)."""
    fields = []
    seen = set()
    with open(CSV_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row["field"].strip()
            if name and name not in seen:
                fields.append(name)
                seen.add(name)
    return fields


def enforce_file(fpath, canonical, canonical_set):
    """
    Enforce canonical field presence and order on every feature in fpath.
    Returns (changed, missing_added, extra_fields).
    """
    with open(fpath, encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    if not features:
        return False, set(), set()

    # Collect extra fields from first feature (schema is uniform per file)
    sample_keys = set(features[0]["properties"].keys())
    extra_fields = sample_keys - canonical_set

    missing_fields = canonical_set - sample_keys

    changed = False

    for feat in features:
        props = feat.get("properties", {})

        # 1. Add missing canonical fields as null
        for field in missing_fields:
            props[field] = None

        # 2. Reorder: canonical fields first (in order), then any extras
        ordered = {f: props[f] for f in canonical if f in props}
        for f in props:
            if f not in canonical_set:
                ordered[f] = props[f]

        if list(ordered.keys()) != list(props.keys()):
            changed = True

        feat["properties"] = ordered

    if missing_fields:
        changed = True

    if changed:
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, separators=(',', ':'))

    return changed, missing_fields, extra_fields


def rebuild_statewide(canonical):
    """Merge all SoV files into a single statewide GeoJSON."""
    sov_files = sorted(SOV_DIR.glob("*.geojson"))
    all_features = []
    for fpath in sov_files:
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)
        all_features.extend(data.get("features", []))
    statewide = {"type": "FeatureCollection", "features": all_features}
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(statewide, f, separators=(',', ':'))
    size_mb = OUT_PATH.stat().st_size / 1_048_576
    print(f"  Rebuilt {OUT_PATH.name}: {len(all_features)} features  ({size_mb:.1f} MB)")


def main():
    canonical = load_canonical_fields()
    canonical_set = set(canonical)
    print(f"Canonical fields: {len(canonical)}")

    sov_files = sorted(SOV_DIR.glob("*.geojson"))
    print(f"Processing {len(sov_files)} town files...\n")

    changed_count  = 0
    all_missing    = {}
    all_extra      = {}

    for fpath in sov_files:
        changed, missing, extra = enforce_file(fpath, canonical, canonical_set)
        if changed:
            changed_count += 1
        if missing:
            all_missing[fpath.name] = sorted(missing)
        if extra:
            all_extra[fpath.name] = sorted(extra)

    # --- Report ---
    if all_missing:
        print("Fields added (null) to files that were missing them:")
        for fname, fields in sorted(all_missing.items()):
            print(f"  {fname}: {fields}")
        print()

    if all_extra:
        print("WARNING — non-canonical fields found (preserved at end of properties):")
        for fname, fields in sorted(all_extra.items()):
            print(f"  {fname}: {fields}")
        print()

    print(f"Files modified: {changed_count} / {len(sov_files)}")

    # --- Rebuild statewide ---
    print("\nRebuilding Vermont_Statewide.geojson...")
    rebuild_statewide(canonical)

    print("\nDone.")


if __name__ == "__main__":
    main()
