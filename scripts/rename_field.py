"""
One-off script: rename Jurisdiction_District_Name -> Municipal_Name
in all .geojson / .geoJSON files under data/State_of_Vermont.
"""
import json
import glob
import os
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SV_DIR = REPO_ROOT / 'data' / 'State_of_Vermont'
OLD_FIELD = 'Jurisdiction_District_Name'
NEW_FIELD = 'Municipal_Name'

sv_files = sorted(
    glob.glob(str(SV_DIR / '*.geojson')) +
    glob.glob(str(SV_DIR / '*.geoJSON'))
)
print(f"Found {len(sv_files)} files to process")

files_changed = 0
total_renamed = 0

for sv_path in sv_files:
    with open(sv_path, encoding='utf-8') as f:
        data = json.load(f)

    file_renamed = 0
    for feat in data.get('features', []):
        props = feat.get('properties')
        if not isinstance(props, dict):
            continue
        if OLD_FIELD in props:
            props[NEW_FIELD] = props.pop(OLD_FIELD)
            file_renamed += 1

    if file_renamed:
        with open(sv_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        files_changed += 1
        total_renamed += file_renamed

print(f"Done. {files_changed} files updated, {total_renamed} fields renamed.")
