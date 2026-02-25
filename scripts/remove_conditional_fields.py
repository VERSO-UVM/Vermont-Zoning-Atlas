"""
One-off script: remove all properties starting with CONDITIONAL_
from all .geojson / .geoJSON files under data/State_of_Vermont.
"""
import json
import glob
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SV_DIR = REPO_ROOT / 'data' / 'State_of_Vermont'
PREFIX = 'CONDITIONAL_'

sv_files = sorted(
    glob.glob(str(SV_DIR / '*.geojson')) +
    glob.glob(str(SV_DIR / '*.geoJSON'))
)
print(f"Found {len(sv_files)} files to process")

files_changed = 0
total_removed = 0

for sv_path in sv_files:
    with open(sv_path, encoding='utf-8') as f:
        data = json.load(f)

    file_removed = 0
    for feat in data.get('features', []):
        props = feat.get('properties')
        if not isinstance(props, dict):
            continue
        keys_to_remove = [k for k in props if k.startswith(PREFIX)]
        for k in keys_to_remove:
            del props[k]
        file_removed += len(keys_to_remove)

    if file_removed:
        with open(sv_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        files_changed += 1
        total_removed += file_removed

print(f"Done. {files_changed} files updated, {total_removed} properties removed.")
