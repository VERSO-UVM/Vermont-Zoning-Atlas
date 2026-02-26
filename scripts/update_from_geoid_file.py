#!/usr/bin/env python3
"""
update_from_geoid_file.py

Compares a new Census GEO_ID file against
data/municipal_geoid_county_rpc_fips.csv and
data/State_of_Vermont/*.geojson, then:

  1. Fills GEO_ID into SoV features that are currently null.
  2. Adds rows to the CSV for SoV files that are missing from it.
  3. Reports municipalities whose GEO_ID cannot be determined.

After running, rebuilds data/RPC/ and data/Vermont_Statewide.geojson.

Usage:
    python scripts/update_from_geoid_file.py <path_to_new_geoid_csv>

The input CSV must have columns: GEOID, NAME
  NAME format: "<Municipality> town/city/village, <County> County, Vermont"
"""

import csv
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOV_DIR = REPO_ROOT / "data" / "State_of_Vermont"
CSV_PATH = REPO_ROOT / "data" / "municipal_geoid_county_rpc_fips.csv"
OUT_PATH = REPO_ROOT / "data" / "Vermont_Statewide.geojson"

RPC_NAMES = {
    "ACRPC": "Addison County Regional Planning Commission",
    "BCRC": "Bennington County Regional Commission",
    "CCRPC": "Chittenden County Regional Planning Commission",
    "CVRPC": "Central Vermont Regional Planning Commission",
    "LCPC": "Lamoille County Planning Commission",
    "MARC": "Mount Ascutney Regional Commission",
    "NVDA": "Northeastern Vermont Development Association",
    "NRPC": "Northwest Regional Planning Commission",
    "RRPC": "Rutland Regional Planning Commission",
    "TRORC": "Two Rivers-Ottauquechee Regional Commission",
    "WRC": "Windham Regional Commission",
}


def norm(s):
    return (
        str(s).strip().replace(" ", "").replace("_", "").replace("-", "").lower()
    )


def parse_new_file(path):
    """Return two dicts: by_geoid and by_norm_name, each -> record dict."""
    by_geoid = {}
    by_name = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            geoid = row["GEOID"].strip()
            name_full = row["NAME"].strip()
            parts = [p.strip() for p in name_full.split(",")]
            muni_raw = parts[0]
            for suffix in [
                " town", " city", " village",
                " gore", " grant", " location",
            ]:
                muni_raw = muni_raw.replace(suffix, "")
            muni_clean = muni_raw.strip()
            county = (
                parts[1].replace(" County", "").strip()
                if len(parts) > 1 else ""
            )
            rec = {
                "geoid": geoid,
                "name_full": name_full,
                "muni_clean": muni_clean,
                "county": county,
            }
            by_geoid[geoid] = rec
            by_name[norm(muni_clean)] = rec
    return by_geoid, by_name


def lookup_new(muni_sov, current_geoid, by_geoid, by_name):
    """Try several normalizations; guard against wrong-county matches."""
    # 1. Exact geoid lookup
    if current_geoid:
        rec = by_geoid.get(str(current_geoid))
        if rec:
            return rec
    # 2. Plain norm match
    rec = by_name.get(norm(muni_sov))
    if rec:
        return rec
    # 3. Strip trailing civic suffix from SoV name (e.g. 'Stowe Town' -> 'Stowe')
    # Only accept Town/Village/City strips — NOT Gore/Grant, which are distinct
    # place types that frequently share names with unrelated towns in other
    # counties (e.g. 'Warren Gore' must not match 'Warren town').
    for suffix in [" Town", " Village", " City"]:
        stripped = muni_sov.replace(suffix, "").strip()
        rec = by_name.get(norm(stripped))
        if rec and norm(stripped) == norm(rec["muni_clean"]):
            return rec
    return None


def load_csv(path):
    """Return list of row dicts and fieldnames."""
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    return rows, fieldnames


def save_csv(path, rows, fieldnames):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def rebuild_statewide():
    sov_files = sorted(SOV_DIR.glob("*.geojson"))
    all_features = []
    for fp in sov_files:
        with open(fp, encoding="utf-8") as f:
            data = json.load(f)
        all_features.extend(data.get("features", []))
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {"type": "FeatureCollection", "features": all_features},
            f,
            separators=(",", ":"),
        )
    size_mb = OUT_PATH.stat().st_size / 1_048_576
    print(
        f"  Rebuilt Vermont_Statewide.geojson: "
        f"{len(all_features)} features  ({size_mb:.1f} MB)"
    )


def main(new_csv_path):
    by_geoid, by_name = parse_new_file(new_csv_path)
    print(f"New file rows: {len(by_geoid)}")

    csv_rows, fieldnames = load_csv(CSV_PATH)
    existing_by_file = {r["file"].strip(): r for r in csv_rows}
    print(f"Existing CSV rows: {len(csv_rows)}")

    sov_files = sorted(SOV_DIR.glob("*.geojson"))
    print(f"SoV files: {len(sov_files)}\n")

    geo_updated = []   # (filename, old_geoid, new_geoid)
    csv_added = []     # filename
    still_null = []    # (filename, muni_name)
    csv_rows_new = list(csv_rows)

    for fpath in sov_files:
        fname = fpath.name
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)

        features = data.get("features", [])
        if not features:
            continue

        props0 = features[0]["properties"]
        muni = str(props0.get("Municipal_Name") or "").strip()
        current_geo = props0.get("GEO_ID")
        rpc = str(props0.get("RPC") or "").strip()
        county = str(props0.get("County") or "").strip()

        csv_row = existing_by_file.get(fname)

        new_rec = lookup_new(muni, current_geo, by_geoid, by_name)
        new_geoid = new_rec["geoid"] if new_rec else None

        # Fill GEO_ID in SoV features if currently null
        if new_geoid and current_geo is None:
            for feat in features:
                feat["properties"]["GEO_ID"] = new_geoid
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, separators=(",", ":"))
            geo_updated.append((fname, current_geo, new_geoid))
        elif new_geoid is None and current_geo is None:
            still_null.append((fname, muni))

        # Add CSV row if file is not already in CSV
        if not csv_row:
            new_row = {
                "file": fname,
                "Municipal_Name": muni,
                "GEO_ID": new_geoid or "",
                "County": new_rec["county"] if new_rec else county,
                "RPC_Name": RPC_NAMES.get(rpc, ""),
                "RPC": rpc,
                "FIPS6": "",
            }
            csv_rows_new.append(new_row)
            csv_added.append(fname)

    csv_rows_new.sort(key=lambda r: r["file"])
    save_csv(CSV_PATH, csv_rows_new, fieldnames)

    print(f"GEO_IDs filled in SoV files: {len(geo_updated)}")
    for fname, old, new in geo_updated:
        print(f"  {fname}: {old!r} -> {new}")

    print(f"\nNew rows added to CSV: {len(csv_added)}")
    for fname in csv_added:
        print(f"  {fname}")

    print(f"\nStill null GEO_ID (no Census match): {len(still_null)}")
    for fname, muni in still_null:
        print(f"  {fname}: {muni!r}")

    print("\nRebuilding RPC files...")
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "merge_state_to_rpc.py")],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    print(result.stdout.strip())
    if result.returncode != 0:
        print("  ERROR:", result.stderr.strip())

    print("\nRebuilding statewide file...")
    rebuild_statewide()
    print("\nDone.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        default = "C:/Users/kefor/Downloads/vt_towns_geoid (1).csv"
        print(f"No path given; using default: {default}")
        main(default)
    else:
        main(sys.argv[1])
