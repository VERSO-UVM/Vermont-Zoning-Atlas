#!/usr/bin/env python3
r"""
Propose field-name mappings to match the canonical list from the CSV.

Reads the CSV list of kept fields and scans State_of_Vermont GeoJSON files to
identify fields that need renaming or dropping. Outputs a CSV of proposals.
"""

import csv
import json
from pathlib import Path
from collections import defaultdict


def normalize(name):
    """Normalize a field name for fuzzy matching."""
    return "".join(ch.lower() for ch in name if ch.isalnum())


def load_csv_fields(csv_path):
    """Load canonical field names from the CSV file."""
    fields = []
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            value = row[0].strip()
            if value:
                fields.append(value)
    return fields


def collect_geojson_fields(state_dir):
    """Collect all unique property fields from State_of_Vermont files."""
    fields = set()
    for file_path in sorted(Path(state_dir).glob("*.geojson")):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            fields.update(props.keys())
    return sorted(fields)


def propose_mappings(csv_fields, geojson_fields):
    """Propose mappings from geojson fields to CSV canonical fields."""
    csv_set = set(csv_fields)
    csv_norm_map = defaultdict(list)
    for name in csv_fields:
        csv_norm_map[normalize(name)].append(name)

    proposals = []
    unmatched = []

    for field in geojson_fields:
        if field in csv_set:
            proposals.append((field, field, "exact"))
            continue

        field_norm = normalize(field)
        matches = csv_norm_map.get(field_norm, [])
        if len(matches) == 1:
            proposals.append((field, matches[0], "normalized"))
        else:
            unmatched.append(field)

    return proposals, unmatched


def write_proposals_csv(output_path, proposals, unmatched):
    """Write mapping proposals to CSV."""
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["source_field", "target_field", "match_type"])
        for source, target, match_type in proposals:
            writer.writerow([source, target, match_type])
        for source in unmatched:
            writer.writerow([source, "", "unmatched"])


def main():
    repo_root = Path(__file__).resolve().parent
    csv_path = repo_root / "data" / "VTZA S26 Kept Attribute Fields (As they appear in table).csv"
    state_dir = repo_root / "data" / "State_of_Vermont"
    output_path = repo_root / "field_mapping_proposals.csv"

    csv_fields = load_csv_fields(csv_path)
    geojson_fields = collect_geojson_fields(state_dir)
    proposals, unmatched = propose_mappings(csv_fields, geojson_fields)

    write_proposals_csv(output_path, proposals, unmatched)

    print("Field mapping proposals written to: field_mapping_proposals.csv")
    print(f"Canonical fields in CSV: {len(csv_fields)}")
    print(f"Unique fields in State_of_Vermont: {len(geojson_fields)}")
    print(f"Proposed mappings: {len(proposals)}")
    print(f"Unmatched fields: {len(unmatched)}")

    if unmatched:
        print("\nSample unmatched fields (first 20):")
        for name in unmatched[:20]:
            print(f"  - {name}")


if __name__ == "__main__":
    main()
