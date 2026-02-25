"""
Fill null values in data/State_of_Vermont from data/temp/vt-zoning-update_standardized.geojson.
Join key: (County, District_Name) — only acts on unique matches (skips ambiguous).
Field names normalised via analysis/field_mapping_change.csv before comparison.
"""
import json, csv, glob
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).parent.parent
SV_DIR    = REPO_ROOT / 'data' / 'State_of_Vermont'
TEMP_FILE = REPO_ROOT / 'data' / 'temp' / 'vt-zoning-update_standardized.geojson'

# ── Build field mapping ───────────────────────────────────────────────────────
mapping    = {}
remove_set = set()
with open(REPO_ROOT / 'analysis' / 'field_mapping_change.csv', newline='') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        if len(row) < 3 or not row[0].strip(): continue
        source, target, match_type = row[0].strip(), row[1].strip(), row[2].strip()
        if match_type == 'Remove':
            remove_set.add(source)
        elif match_type == 'Replace' and target:
            mapping[source] = target

# ── Normalise temp feature properties to canonical field names ────────────────
with open(TEMP_FILE) as f:
    temp_data = json.load(f)

def normalise(props):
    out = {}
    for k, v in props.items():
        if k in remove_set:
            continue
        canonical = mapping.get(k, k)
        if canonical not in out or (out[canonical] is None and v is not None):
            out[canonical] = v
    return out

temp_features = []
for feat in temp_data.get('features', []):
    p = normalise(feat.get('properties') or {})
    temp_features.append(p)

# ── Build join index: (County, District_Name) -> list of normalised temp props ─
temp_index = defaultdict(list)
for p in temp_features:
    county = (p.get('County') or '').strip()
    dist   = (p.get('District_Name') or '').strip()
    if county and dist:
        temp_index[(county, dist)].append(p)

unique_index = {k: v[0] for k, v in temp_index.items() if len(v) == 1}
print(f"Unique join keys available: {len(unique_index)}")

# ── Load all SV files and fill nulls ─────────────────────────────────────────
sv_files = sorted(SV_DIR.glob('*.geojson'))
print(f"SV files to scan: {len(sv_files)}")

total_filled = 0
files_changed = 0

for sv_path in sv_files:
    with open(sv_path) as f:
        data = json.load(f)

    file_filled = 0
    for feat in data.get('features', []):
        props = feat.get('properties')
        if not isinstance(props, dict): continue

        county = (props.get('County') or '').strip()
        dist   = (props.get('District_Name') or '').strip()
        key    = (county, dist)
        src    = unique_index.get(key)
        if not src:
            continue

        for field, src_val in src.items():
            if src_val is None or src_val == '':
                continue
            if field not in props:
                continue   # only fill fields already in schema
            cur = props.get(field)
            if cur is None or cur == '':
                props[field] = src_val
                file_filled += 1

    if file_filled:
        with open(sv_path, 'w') as f:
            json.dump(data, f, indent=2)
        files_changed += 1
        total_filled += file_filled
        print(f"  {sv_path.name}: {file_filled} values filled")

print(f"\nDone. {files_changed} files updated, {total_filled} null values filled.")
