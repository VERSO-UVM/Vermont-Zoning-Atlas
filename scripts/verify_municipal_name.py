"""
Verify (and optionally fix) that Municipal_Name in each file matches
the municipality extracted from the filename.

Filename pattern: {County}_{Municipality}_rev{date}.{ext}
e.g. Addison_Middlebury_rev09132022.geojson -> expected Municipal_Name = "Middlebury"
"""
import json
import csv
import glob
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SV_DIR = REPO_ROOT / 'data' / 'State_of_Vermont'
REPORT_CSV = REPO_ROOT / 'analysis' / 'municipal_name_mismatches.csv'
FIX = True  # Set to False to report only without modifying files

sv_files = sorted(
    glob.glob(str(SV_DIR / '*.geojson')) +
    glob.glob(str(SV_DIR / '*.geoJSON'))
)
print(f"Found {len(sv_files)} files to check")

mismatches = []   # (file, expected, found)
files_fixed = 0
total_fixed = 0
files_ok = 0

for sv_path in sv_files:
    stem = Path(sv_path).stem  # e.g. Addison_Middlebury_rev09132022

    # Strip _rev and everything after it, then take everything after first underscore
    name_part = re.sub(r'_rev.*$', '', stem, flags=re.IGNORECASE)
    parts = name_part.split('_', 1)
    if len(parts) < 2:
        print(f"  SKIP (unexpected filename format): {stem}")
        continue
    expected = parts[1]  # e.g. "Middlebury" or "WoodstockVillage"

    with open(sv_path, encoding='utf-8') as f:
        data = json.load(f)

    file_mismatches = 0
    for feat in data.get('features', []):
        props = feat.get('properties')
        if not isinstance(props, dict):
            continue
        current = props.get('Municipal_Name', '')
        if current != expected:
            mismatches.append({
                'file': stem,
                'expected': expected,
                'found': current,
            })
            file_mismatches += 1
            if FIX:
                props['Municipal_Name'] = expected

    if file_mismatches and FIX:
        with open(sv_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        files_fixed += 1
        total_fixed += file_mismatches
        print(f"  FIXED {stem}: {file_mismatches} features (was '{mismatches[-1]['found']}' → '{expected}')")
    elif not file_mismatches:
        files_ok += 1

# Write report CSV
with open(REPORT_CSV, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['file', 'expected', 'found'])
    writer.writeheader()
    writer.writerows(mismatches)

print()
print(f"Files with correct Municipal_Name: {files_ok}")
print(f"Files with mismatches:             {len(set(m['file'] for m in mismatches))}")
if FIX:
    print(f"Features fixed:                    {total_fixed}")
print(f"Report written to: {REPORT_CSV}")
