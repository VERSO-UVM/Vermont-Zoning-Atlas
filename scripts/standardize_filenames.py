"""
1. Strip " County" suffix from County field in all features
2. Rename all files to {County}_{Municipal_Name}.geojson
3. Merge any files that share the same target name
"""
import json, glob, os, re
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).parent.parent
SV_DIR    = REPO_ROOT / 'data' / 'State_of_Vermont'

sv_files = sorted(
    glob.glob(str(SV_DIR / '*.geojson')) +
    glob.glob(str(SV_DIR / '*.geoJSON'))
)
print(f"Found {len(sv_files)} files\n")

# ── Step 1: normalise County field in every feature ───────────────────────────
county_fixed = 0
for sv_path in sv_files:
    with open(sv_path, encoding='utf-8') as f:
        data = json.load(f)
    changed = False
    for feat in data.get('features', []):
        props = feat.get('properties') or {}
        c = props.get('County') or ''
        if c.endswith(' County'):
            props['County'] = c[:-7]   # strip " County"
            county_fixed += 1
            changed = True
    if changed:
        with open(sv_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
print(f"County field normalised on {county_fixed} features\n")

# ── Step 2: group files by target name {County}_{Municipal_Name} ──────────────
# Re-read after normalisation
sv_files = sorted(
    glob.glob(str(SV_DIR / '*.geojson')) +
    glob.glob(str(SV_DIR / '*.geoJSON'))
)

groups = defaultdict(list)   # target_stem -> [current_path, ...]

for sv_path in sv_files:
    with open(sv_path, encoding='utf-8') as f:
        data = json.load(f)
    county = muni = None
    for feat in data.get('features', []):
        props = feat.get('properties') or {}
        if not county: county = props.get('County') or ''
        if not muni:   muni   = props.get('Municipal_Name') or ''
        if county and muni: break
    if not county or not muni:
        print(f"  WARNING: no County/Municipal_Name in {Path(sv_path).name}, skipping")
        continue
    groups[f"{county}_{muni}"].append(sv_path)

merges  = {t: p for t, p in groups.items() if len(p) > 1}
singles = {t: p for t, p in groups.items() if len(p) == 1}
print(f"Files to rename (no merge): {len(singles)}")
print(f"Groups to merge:            {len(merges)}")
if merges:
    print()
    for t, paths in sorted(merges.items()):
        print(f"  MERGE -> {t}.geojson")
        for p in paths:
            print(f"    {Path(p).name}")
print()

# ── Step 3: rename single files ───────────────────────────────────────────────
renamed = 0
for target_stem, paths in singles.items():
    src = Path(paths[0])
    dst = SV_DIR / f"{target_stem}.geojson"
    if src == dst:
        continue
    if dst.exists():
        print(f"  CONFLICT: {dst.name} already exists, skipping {src.name}")
        continue
    src.rename(dst)
    renamed += 1

print(f"Files renamed: {renamed}")

# ── Step 4: merge groups ──────────────────────────────────────────────────────
merged_groups = 0
for target_stem, paths in sorted(merges.items()):
    dst = SV_DIR / f"{target_stem}.geojson"

    # Collect all features; rich files (.geojson) first, stubs (.geoJSON) last
    all_features = []
    geojson_type = None
    for p in sorted(paths, key=lambda x: (x.endswith('.geoJSON'), x)):
        with open(p, encoding='utf-8') as f:
            data = json.load(f)
        if geojson_type is None:
            geojson_type = data.get('type', 'FeatureCollection')
        all_features.extend(data.get('features', []))

    merged_data = {'type': geojson_type, 'features': all_features}
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=2)

    # Delete originals (skip if one is already the target)
    for p in paths:
        if Path(p) != dst:
            os.remove(p)

    print(f"  MERGED {len(paths)} files -> {dst.name} ({len(all_features)} features)")
    merged_groups += 1

print(f"\nDone.")
print(f"  Renamed:      {renamed} files")
print(f"  Merged groups:{merged_groups}")
final = list(SV_DIR.glob('*.geojson')) + list(SV_DIR.glob('*.geoJSON'))
print(f"  Files now:    {len(final)}")
