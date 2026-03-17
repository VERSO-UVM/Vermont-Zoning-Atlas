#!/usr/bin/env python3
"""
build_statewide.py

Merges all individual town GeoJSON files from data/State_of_Vermont/ into a
single statewide FeatureCollection at data/Vermont_Statewide.geojson.

Re-run this script any time SoV town files are edited.

Usage:
    python scripts/build_statewide.py
"""

import json
from pathlib import Path

REPO_ROOT   = Path(__file__).resolve().parent.parent
SOV_DIR     = REPO_ROOT / "data" / "State_of_Vermont"
OUT_PATH    = REPO_ROOT / "data" / "Vermont_Statewide.geojson"


def main():
    sov_files = sorted(SOV_DIR.glob("*.geojson"))
    print(f"Reading {len(sov_files)} town files from {SOV_DIR.name}/...")

    all_features = []
    for fpath in sov_files:
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)
        feats = data.get("features", [])
        all_features.extend(feats)

    print(f"Total features: {len(all_features)}")

    statewide = {"type": "FeatureCollection", "features": all_features}
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(statewide, f, separators=(',', ':'))

    size_mb = OUT_PATH.stat().st_size / 1_048_576
    print(f"Written to {OUT_PATH.relative_to(REPO_ROOT)}  ({size_mb:.1f} MB)")
    print("Done.")


if __name__ == "__main__":
    main()
