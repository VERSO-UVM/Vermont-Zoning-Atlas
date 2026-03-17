"""
Assign a globally unique sequential OBJECT_ID (1-based) to every feature
across all data/State_of_Vermont files, in alphabetical file order.
"""
import json
import glob
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SV_DIR = REPO_ROOT / 'data' / 'State_of_Vermont'

sv_files = sorted(
    glob.glob(str(SV_DIR / '*.geojson')) +
    glob.glob(str(SV_DIR / '*.geoJSON'))
)
print(f"Found {len(sv_files)} files")

next_id = 1

for sv_path in sv_files:
    with open(sv_path, encoding='utf-8') as f:
        data = json.load(f)

    for feat in data.get('features', []):
        props = feat.get('properties')
        if isinstance(props, dict):
            props['OBJECT_ID'] = next_id
            next_id += 1

    with open(sv_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

print(f"Assigned OBJECT_IDs 1–{next_id - 1} across {len(sv_files)} files.")
