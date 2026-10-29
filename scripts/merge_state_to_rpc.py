#!/usr/bin/env python3
"""
merge_state_to_rpc.py

Compiles individual town GeoJSON files from data/State_of_Vermont/ into
per-RPC files in data/RPC/.

RPC is determined in priority order:
  1. The 'RPC' property already set on each feature (VCGI 2-character code)
  2. Lookup via data/municipal_geoid_county_rpc_fips.csv using normalized JXTN
  3. Manual overrides for municipalities not in the CSV

Output files keep the RPC abbreviations (e.g. ACRPC.geojson) used by the site.

Usage:
    python scripts/merge_state_to_rpc.py
"""

import csv
import json
import os
from pathlib import Path

# --- Paths ---
REPO_ROOT   = Path(__file__).resolve().parent.parent
SOV_DIR     = REPO_ROOT / "data" / "State_of_Vermont"
RPC_DIR     = REPO_ROOT / "data" / "RPC"
CSV_PATH    = REPO_ROOT / "data" / "municipal_geoid_county_rpc_fips.csv"

# --- Manual RPC assignments for municipalities absent from the CSV ---
MANUAL_RPC = {
    "huntington":      "CC",
    "morristown":      "LC",
    "northbennington": "BC",
    "oldbennington":   "BC",
    "saintgeorge":     "CC",
    "sandgatef2":      "BC",
    "southburlington": "CC",
    "stowetown":       "LC",
    "stovevillage":    "LC",
    "warrengore":      "NV",
}

# --- VCGI 2-character RPC code -> output file name ---
RPC_FILES = {
    "AC": "ACRPC",
    "BC": "BCRC",
    "CC": "CCRPC",
    "CV": "CVRPC",
    "LC": "LCPC",
    "MA": "MARC",
    "NV": "NVDA",
    "NW": "NRPC",
    "RR": "RRPC",
    "TR": "TRORC",
    "WR": "WRC",
}
CSV_RPC_CODES = {abbr: code for code, abbr in RPC_FILES.items()}


def norm(s):
    """Normalize a string for fuzzy matching."""
    if not s:
        return ""
    return str(s).strip().replace(" ", "").replace("_", "").replace("-", "").lower()


def build_csv_lookup():
    """Return dict: norm(municipal_name) -> VCGI RPC code."""
    lookup = {}
    with open(CSV_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            lookup[norm(row["Municipal_Name"])] = CSV_RPC_CODES.get(row["RPC"], row["RPC"])
    return lookup


def get_rpc(props, csv_lookup):
    """Resolve RPC for a feature, checking property field first, then CSV, then manual."""
    # 1. Use the RPC field already on the feature
    rpc = (props.get("RPC") or "").strip()
    if rpc:
        return rpc

    # 2. Look up by JXTN in the CSV
    muni = str(props.get("JXTN") or "").strip()
    rpc = csv_lookup.get(norm(muni))
    if rpc:
        return rpc

    # 3. Manual overrides
    return MANUAL_RPC.get(norm(muni))


def main():
    csv_lookup = build_csv_lookup()

    rpc_features = {}
    no_rpc = []

    sov_files = sorted(SOV_DIR.glob("*.geojson"))
    print(f"Reading {len(sov_files)} town files from {SOV_DIR.name}/...")

    for fpath in sov_files:
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)

        for feat in data.get("features", []):
            props = feat.get("properties", {})
            # Strip trailing spaces from JXTN
            if "JXTN" in props and props["JXTN"]:
                props["JXTN"] = str(props["JXTN"]).strip()

            rpc = get_rpc(props, csv_lookup)
            if rpc:
                rpc_features.setdefault(rpc, []).append(feat)
            else:
                muni = str(props.get("JXTN") or "").strip()
                no_rpc.append((fpath.name, muni))

    print(f"\nWriting RPC files to {RPC_DIR}/...")
    for rpc in sorted(rpc_features):
        feats = rpc_features[rpc]
        out_path = RPC_DIR / f"{RPC_FILES.get(rpc, rpc)}.geojson"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": feats}, f)
        munis = sorted(set(ft["properties"].get("JXTN", "") for ft in feats))
        print(f"  {out_path.name}: {len(feats):>4} features, {len(munis):>2} municipalities")

    if no_rpc:
        unique = sorted(set(m for _, m in no_rpc if m))
        print(f"\nWARNING: {len(no_rpc)} features had no RPC match:")
        for m in unique:
            print(f"  '{m}'")
    else:
        print("\nAll features matched to an RPC.")

    print("\nDone.")


if __name__ == "__main__":
    main()
