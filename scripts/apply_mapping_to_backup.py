import json
import csv
import os
from pathlib import Path

# Paths relative to repo root
REPO_ROOT = Path(__file__).parent.parent
CSV_PATH = REPO_ROOT / 'analysis' / 'field_mapping_change.csv'
BACKUP_DIR = REPO_ROOT / 'data' / 'GIT Backup data' / 'State_of_Vermont'

# Read the field mapping CSV
mapping = {}       # source -> target (Replace rows where source != target)
remove_fields = set()  # fields to drop entirely

with open(CSV_PATH, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        source = row['source_field'].strip()
        target = row['target_field'].strip()
        match_type = row['match_type'].strip()

        if not source:
            continue
        if match_type == 'Remove':
            remove_fields.add(source)
        elif match_type == 'Replace' and target and source != target:
            mapping[source] = target

print(f"Loaded {len(mapping)} field renames and {len(remove_fields)} field removals")

# Find all GeoJSON files (both .geojson and .geoJSON)
geojson_files = list(BACKUP_DIR.glob('*.geojson')) + list(BACKUP_DIR.glob('*.geoJSON'))
geojson_files.sort()
print(f"Found {len(geojson_files)} GeoJSON files to process")
print()

total_renamed = 0
total_removed = 0
errors = []

for geojson_file in geojson_files:
    try:
        with open(geojson_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        file_renamed = 0
        file_removed = 0

        for feature in data.get('features', []):
            if not feature.get('properties'):
                continue

            old_props = feature['properties']
            new_props = {}

            for key, value in old_props.items():
                if key in remove_fields:
                    file_removed += 1
                elif key in mapping:
                    new_props[mapping[key]] = value
                    file_renamed += 1
                else:
                    new_props[key] = value

            feature['properties'] = new_props

        # Write back in-place
        with open(geojson_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        total_renamed += file_renamed
        total_removed += file_removed
        print(f"  {geojson_file.name}: {file_renamed} renamed, {file_removed} removed")

    except Exception as e:
        errors.append((geojson_file.name, str(e)))
        print(f"  ERROR {geojson_file.name}: {e}")

print()
print(f"Done. {len(geojson_files) - len(errors)} files updated successfully.")
print(f"Total fields renamed: {total_renamed}")
print(f"Total fields removed: {total_removed}")
if errors:
    print(f"\nErrors ({len(errors)}):")
    for fname, err in errors:
        print(f"  {fname}: {err}")
