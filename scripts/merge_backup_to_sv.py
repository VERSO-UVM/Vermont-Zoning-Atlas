import json
import csv
import os
import glob
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
BACKUP_DIR = REPO_ROOT / 'data' / 'GIT Backup data' / 'State_of_Vermont'
SV_DIR = REPO_ROOT / 'data' / 'State_of_Vermont'
CONFLICT_CSV = REPO_ROOT / 'analysis' / 'merge_conflicts.csv'

# Field name aliases: backup name -> canonical current name
# Needed because backup was transformed before the final ABB_DIST_NAME target was settled
FIELD_ALIASES = {
    'Abbreviated_Jurisdiction_District_Name': 'Abbreviated_District_Name'
}

SENTINEL = object()  # marks a field as absent from current

sv_files = sorted(
    glob.glob(str(SV_DIR / '*.geojson')) +
    glob.glob(str(SV_DIR / '*.geoJSON'))
)
print(f"Found {len(sv_files)} State_of_Vermont files to process")

conflicts = []
total_filled = 0
total_added = 0
files_updated = 0
files_skipped = 0
unmatched_features = 0

for sv_path in sv_files:
    basename = os.path.basename(sv_path)
    backup_path = BACKUP_DIR / basename

    if not backup_path.exists():
        print(f"  SKIP (no backup): {basename}")
        files_skipped += 1
        continue

    with open(sv_path, encoding='utf-8') as f:
        sv_data = json.load(f)
    with open(backup_path, encoding='utf-8') as f:
        backup_data = json.load(f)

    # Build lookup: Jurisdiction_District_Name -> feature for backup
    backup_lookup = {}
    for feat in backup_data.get('features', []):
        props = feat.get('properties') or {}
        key = props.get('Jurisdiction_District_Name')
        if key:
            backup_lookup[key] = props

    file_filled = 0
    file_added = 0
    file_conflicts = 0
    file_unmatched = 0

    for feat in sv_data.get('features', []):
        if not isinstance(feat.get('properties'), dict):
            continue

        sv_props = feat['properties']
        district_name = sv_props.get('Jurisdiction_District_Name')

        if not district_name or district_name not in backup_lookup:
            file_unmatched += 1
            continue

        backup_props = backup_lookup[district_name]

        for backup_field, backup_value in backup_props.items():
            # Skip empty backup values — nothing useful to contribute
            if backup_value is None or backup_value == '':
                continue

            canonical = FIELD_ALIASES.get(backup_field, backup_field)
            current_value = sv_props.get(canonical, SENTINEL)

            if current_value is SENTINEL:
                # Field entirely missing from current — add it
                sv_props[canonical] = backup_value
                file_added += 1
            elif current_value == '':
                # Field present but empty — fill from backup
                sv_props[canonical] = backup_value
                file_filled += 1
            elif current_value != backup_value:
                # Both non-empty but different — current wins, log conflict
                conflicts.append({
                    'file': basename,
                    'district_name': district_name,
                    'field': canonical,
                    'current_value': current_value,
                    'backup_value': backup_value,
                })
                file_conflicts += 1

    # Write updated file in-place (geometry untouched, only properties changed)
    with open(sv_path, 'w', encoding='utf-8') as f:
        json.dump(sv_data, f, indent=2)

    total_filled += file_filled
    total_added += file_added
    unmatched_features += file_unmatched
    files_updated += 1

    if file_filled or file_added or file_conflicts or file_unmatched:
        print(f"  {basename}: filled={file_filled} added={file_added} "
              f"conflicts={file_conflicts} unmatched_features={file_unmatched}")

# Write conflict CSV
with open(CONFLICT_CSV, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(
        f, fieldnames=['file', 'district_name', 'field', 'current_value', 'backup_value']
    )
    writer.writeheader()
    writer.writerows(conflicts)

print()
print(f"Done. {files_updated} files updated, {files_skipped} skipped.")
print(f"Total values filled in (empty → backup): {total_filled}")
print(f"Total fields added (missing → backup):    {total_added}")
print(f"Total conflicts logged (both non-empty):  {len(conflicts)}")
print(f"Total unmatched features (no backup):     {unmatched_features}")
print(f"Conflict report: {CONFLICT_CSV}")
