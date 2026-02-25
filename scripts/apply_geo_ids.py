"""
Apply GEO_ID to all features in data/State_of_Vermont using vt_towns_geoid.csv,
matching on Municipal_Name + County.
"""
import json, csv, glob, re
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).parent.parent
SV_DIR    = REPO_ROOT / 'data' / 'State_of_Vermont'

# ── Load GEOID lookup ──────────────────────────────────────────────────────────
geoid_rows = []
with open(REPO_ROOT / 'data' / 'vt_towns_geoid.csv') as f:
    for row in csv.DictReader(f):
        name_full  = row['NAME']
        parts      = [p.strip() for p in name_full.split(',')]
        place_raw  = parts[0]
        county_raw = parts[1]
        place_name  = re.sub(r'\s+(town|city|village|gore|grant|unorganized territory)$',
                             '', place_raw, flags=re.I).strip()
        county_name = re.sub(r'\s+County$', '', county_raw, flags=re.I).strip()
        geoid_rows.append({'geoid': row['GEOID'], 'place_name': place_name,
                           'county_name': county_name})

def norm(s):
    return re.sub(r'\s+', ' ', s.lower().replace("'", "").replace(".", "")).strip()

lookup    = {(norm(r['place_name']), norm(r['county_name'])): r['geoid'] for r in geoid_rows}
by_place  = defaultdict(list)
for r in geoid_rows:
    by_place[norm(r['place_name'])].append(r)

# ── Manual overrides (confirmed by user) ─────────────────────────────────────
MANUAL = {
    ('Enosburghfalls',          'Franklin'):  '5001124050',  # Enosburgh town
    ('JohnsonTownJohnsonVillage','Lamoille'):  '5001537075',  # Johnson town
    ('Morristown_Morrisville',  'Lamoille'):  '5001546675',  # Morristown town
    ('OldBennington',           'Bennington'):'5000304825',  # Bennington town
}

# ── Overlay/district suffix stripping ─────────────────────────────────────────
OVERLAY_RE = re.compile(
    r'_(?:Overlay|Overlays|ARO|FEHO|FHO|HCVO|Flood|Meadow|FBCOoverlay)$', re.I)

TYPE_RE = re.compile(r'\s+(Town|City|Village|Gore|Grant)$', re.I)

def resolve(muni_raw, county_raw):
    county = re.sub(r'\s+County$', '', county_raw, flags=re.I).strip()

    # Manual overrides first
    key = (muni_raw, county)
    if key in MANUAL:
        return MANUAL[key]

    # Strip overlay suffixes, split CamelCase, normalise Saint/St
    base = OVERLAY_RE.sub('', muni_raw)
    base = re.sub(r'([a-z])([A-Z])', r'\1 \2', base)
    base = re.sub(r'^Saint\s+', 'St. ', base)
    base = re.sub(r'^St\b(?!\.)', 'St.', base)

    for candidate in [base, TYPE_RE.sub('', base).strip()]:
        exact = lookup.get((norm(candidate), norm(county)))
        if exact:
            return exact
        # County-filtered fallback
        matches = [r for r in by_place.get(norm(candidate), [])
                   if norm(r['county_name']) == norm(county)]
        if len(matches) == 1:
            return matches[0]['geoid']
        # Single global match
        all_m = by_place.get(norm(candidate), [])
        if len(all_m) == 1:
            return all_m[0]['geoid']

    return None

# ── Apply to all files ─────────────────────────────────────────────────────────
sv_files = sorted(
    glob.glob(str(SV_DIR / '*.geojson')) +
    glob.glob(str(SV_DIR / '*.geoJSON'))
)
print(f"Found {len(sv_files)} files")

applied  = 0
skipped  = 0
unresolved = set()

for sv_path in sv_files:
    basename = Path(sv_path).name
    with open(sv_path, encoding='utf-8') as f:
        data = json.load(f)

    changed = False
    for feat in data.get('features', []):
        props = feat.get('properties')
        if not isinstance(props, dict):
            continue
        muni   = (props.get('Municipal_Name') or '').strip()
        county = (props.get('County') or '').strip()
        if not muni:
            skipped += 1
            continue
        geoid = resolve(muni, county)
        if geoid:
            props['GEO_ID'] = geoid
            applied += 1
            changed = True
        else:
            unresolved.add((muni, county, basename))
            skipped += 1

    if changed:
        with open(sv_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

print(f"\nGEO_IDs applied:  {applied}")
print(f"Skipped/unresolved: {skipped}")
if unresolved:
    print("\nUnresolved:")
    for muni, county, fname in sorted(unresolved):
        print(f"  '{muni}'  County='{county}'  {fname}")
else:
    print("All features resolved.")
