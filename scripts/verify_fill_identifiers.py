#!/usr/bin/env python3
"""
verify_fill_identifiers.py

For every GeoJSON in data/State_of_Vermont/, checks that GEO_ID, County,
Municipal_Name, and RPC are non-null on every feature.

Where values are missing:
  - Looks up the correct value from data/municipal_geoid_county_rpc_fips.csv
    (keyed first by filename, then by normalized Municipal_Name as fallback).
  - If still not found, sets the field to null and records it for reporting.

Saves modified files in place and rebuilds Vermont_Statewide.geojson.

Usage:
    python scripts/verify_fill_identifiers.py
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOV_DIR   = REPO_ROOT / "data" / "State_of_Vermont"
CSV_PATH  = REPO_ROOT / "data" / "municipal_geoid_county_rpc_fips.csv"
OUT_PATH  = REPO_ROOT / "data" / "Vermont_Statewide.geojson"

FIELDS = ["GEO_ID", "County", "Municipal_Name", "RPC"]


def norm(s):
    if not s:
        return ""
    return str(s).strip().replace(" ", "").replace("_", "").replace("-", "").lower()


def load_csv_lookup():
    """
    Returns two dicts:
      by_file  : filename (str) -> row dict
      by_muni  : norm(Municipal_Name) -> row dict
    """
    by_file = {}
    by_muni = {}
    with open(CSV_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fname = row["file"].strip()
            mname = row["Municipal_Name"].strip()
            by_file[fname] = row
            by_muni[norm(mname)] = row
    return by_file, by_muni


def get_csv_value(field, csv_row):
    """Return non-empty value from csv_row for the given field, else None."""
    if csv_row is None:
        return None
    v = csv_row.get(field, "").strip()
    return v if v else None


def is_empty(val):
    if val is None:
        return True
    return str(val).strip() == ""


def process_file(fpath, by_file, by_muni):
    """
    Audit and fill GEO_ID, County, Municipal_Name, RPC for every feature.
    Returns (changed, unfilled) where unfilled is a list of
    (feature_index, field_name) pairs that could not be filled.
    """
    with open(fpath, encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    if not features:
        return False, []

    # Resolve CSV row: prefer by filename, then by muni name from first feature
    csv_row = by_file.get(fpath.name)
    if csv_row is None:
        first_muni = str(features[0]["properties"].get("Municipal_Name") or "").strip()
        csv_row = by_muni.get(norm(first_muni))

    changed = False
    unfilled = []  # (feat_idx, field_name)

    for idx, feat in enumerate(features):
        props = feat.get("properties", {})

        for field in FIELDS:
            if not is_empty(props.get(field)):
                continue  # already filled

            # Try CSV lookup
            filled_val = get_csv_value(field, csv_row)

            if filled_val:
                # Convert GEO_ID to string to preserve leading zeros
                props[field] = str(filled_val) if field == "GEO_ID" else filled_val
                changed = True
            else:
                props[field] = None
                unfilled.append((idx, field))

    if changed:
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, separators=(',', ':'))

    return changed, unfilled


def rebuild_statewide():
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
    by_file, by_muni = load_csv_lookup()

    sov_files = sorted(SOV_DIR.glob("*.geojson"))
    print(f"Checking {len(sov_files)} town files for GEO_ID, County, Municipal_Name, RPC...\n")

    filled_count   = 0          # files where at least one value was filled in
    still_null     = defaultdict(list)   # field -> [filename]

    for fpath in sov_files:
        changed, unfilled = process_file(fpath, by_file, by_muni)
        if changed:
            filled_count += 1
        for (idx, field) in unfilled:
            if fpath.name not in still_null[field]:
                still_null[field].append(fpath.name)

    # --- Summary ---
    print(f"Files updated (values filled from CSV): {filled_count}")

    if still_null:
        print()
        print("=" * 60)
        print("COULD NOT FILL — set to null (manual review needed):")
        print("=" * 60)
        for field in FIELDS:
            files = still_null.get(field, [])
            if files:
                print(f"\n  {field} ({len(files)} file{'s' if len(files) != 1 else ''}):")
                for fname in sorted(files):
                    print(f"    {fname}")
    else:
        print("\nAll GEO_ID, County, Municipal_Name, and RPC fields are populated.")

    print("\nRebuilding Vermont_Statewide.geojson...")
    rebuild_statewide()
    print("\nDone.")


if __name__ == "__main__":
    main()
