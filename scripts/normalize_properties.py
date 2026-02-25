"""
Normalize properties in all data/State_of_Vermont GeoJSON files:
  1. Rename fields per field_mapping_change.csv (match_type=Replace, source→target)
  2. Remove fields (match_type=Remove)
  3. STOP if any field is found that isn't listed in source_field at all
  4. Add any target fields missing from a feature as null
  5. Order properties by the 'order' column
  6. Write a final audit CSV: field name + count of non-null values across all files
"""
import json
import csv
import glob
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CSV_PATH   = REPO_ROOT / 'analysis' / 'field_mapping_change.csv'
SV_DIR     = REPO_ROOT / 'data' / 'State_of_Vermont'
AUDIT_CSV  = REPO_ROOT / 'analysis' / 'property_key_audit.csv'

# ── Build mappings from CSV ───────────────────────────────────────────────────
replace_map  = {}   # source_field -> target_field
remove_set   = set()
target_order = {}   # target_field -> float order (first seen wins)

with open(CSV_PATH, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # skip header
    for row in reader:
        if len(row) < 3 or not row[0].strip():
            continue
        source     = row[0].strip()
        target     = row[1].strip()
        match_type = row[2].strip()
        order_val  = row[3].strip() if len(row) > 3 else ''

        if match_type == 'Remove':
            remove_set.add(source)
        elif match_type == 'Replace':
            replace_map[source] = target
            if order_val and target and target not in target_order:
                try:
                    target_order[target] = float(order_val)
                except ValueError:
                    pass

all_known     = set(replace_map.keys()) | remove_set
canonical_fields = [t for t, _ in sorted(target_order.items(), key=lambda x: x[1])]

print(f"Loaded {len(replace_map)} Replace mappings, {len(remove_set)} Remove fields")
print(f"Canonical schema: {len(canonical_fields)} fields")
print()

# ── Process files ─────────────────────────────────────────────────────────────
sv_files = sorted(
    glob.glob(str(SV_DIR / '*.geojson')) +
    glob.glob(str(SV_DIR / '*.geoJSON'))
)
print(f"Found {len(sv_files)} files to process")
print()

value_counts = defaultdict(int)

for sv_path in sv_files:
    basename = Path(sv_path).name

    with open(sv_path, encoding='utf-8') as f:
        data = json.load(f)

    # ── Pass 1: check for unknown fields ─────────────────────────────────────
    stop = False
    for feat_idx, feat in enumerate(data.get('features', [])):
        props = feat.get('properties')
        if not isinstance(props, dict):
            continue
        for key in props:
            if key not in all_known:
                print(f"UNKNOWN FIELD — file: {basename}, "
                      f"feature index: {feat_idx}, field: '{key}'")
                stop = True
    if stop:
        print("\nStopping. Fix unknown fields before continuing.")
        sys.exit(1)

    # ── Pass 2: transform properties ─────────────────────────────────────────
    for feat in data.get('features', []):
        props = feat.get('properties')
        if not isinstance(props, dict):
            continue

        # Apply renames and removals, handling collisions (first non-null wins)
        raw = {}
        for key, val in props.items():
            if key in remove_set:
                continue
            tgt = replace_map.get(key, key)
            if tgt not in raw or (raw[tgt] is None and val is not None):
                raw[tgt] = val

        # Build final ordered properties; add missing canonical fields as null
        new_props = OrderedDict()
        for field in canonical_fields:
            new_props[field] = raw.get(field, None)

        feat['properties'] = new_props

    with open(sv_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    # Count non-null values for audit
    for feat in data.get('features', []):
        props = feat.get('properties')
        if not isinstance(props, dict):
            continue
        for key, val in props.items():
            if val is not None and val != '':
                value_counts[key] += 1

    print(f"  OK  {basename}")

# ── Write audit CSV ───────────────────────────────────────────────────────────
with open(AUDIT_CSV, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['field', 'features_with_value'])
    writer.writeheader()
    for field in canonical_fields:
        writer.writerow({
            'field': field,
            'features_with_value': value_counts.get(field, 0),
        })

print()
print(f"Done. Audit written to: {AUDIT_CSV}")
