"""
Scan all .geojson / .geoJSON files in data/State_of_Vermont and produce a CSV with:
  - Every unique property key seen across all features
  - Count of features that have a non-empty value for that key
  - Count of features that have an empty / null value for that key
  - Total features the key appeared in
"""
import json
import csv
import glob
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SV_DIR = REPO_ROOT / 'data' / 'State_of_Vermont'
OUT_CSV = REPO_ROOT / 'analysis' / 'property_key_audit.csv'

sv_files = sorted(
    glob.glob(str(SV_DIR / '*.geojson')) +
    glob.glob(str(SV_DIR / '*.geoJSON'))
)
print(f"Found {len(sv_files)} files to scan")

has_value   = defaultdict(int)   # key -> features with non-empty value
is_empty    = defaultdict(int)   # key -> features with empty/null value
total_seen  = defaultdict(int)   # key -> total features containing this key

for sv_path in sv_files:
    with open(sv_path, encoding='utf-8') as f:
        data = json.load(f)
    for feat in data.get('features', []):
        props = feat.get('properties')
        if not isinstance(props, dict):
            continue
        for key, val in props.items():
            total_seen[key] += 1
            if val is None or val == '':
                is_empty[key] += 1
            else:
                has_value[key] += 1

all_keys = sorted(total_seen.keys())
print(f"Found {len(all_keys)} unique property keys")

with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'field', 'features_with_value', 'features_empty_or_null', 'total_features_seen'
    ])
    writer.writeheader()
    for key in all_keys:
        writer.writerow({
            'field': key,
            'features_with_value': has_value[key],
            'features_empty_or_null': is_empty[key],
            'total_features_seen': total_seen[key],
        })

print(f"Report written to: {OUT_CSV}")
