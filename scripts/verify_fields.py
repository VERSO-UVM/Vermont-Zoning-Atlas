import json
from pathlib import Path

# Expected fields from index.html map
expected_fields = [
    "County",
    "Jurisdiction_District_Name",
    "District_Type",
    "District_Name",
    "Overlay_District",
    "F1F_Allowance",
    "F2F_Allowance",
    "F3F_Allowance",
    "F4F_Allowance",
    "Affordable_Housing_District",
    "ADU_Owner_Occupancy_Required",
    "F1F_Elderly_Housing_Only",
    "F2F_Elderly_Housing_Only",
    "F3F_Elderly_Housing_Only",
    "F4F_Elderly_Housing_Only"
]

# Check files
files_to_check = [
    'data/State_of_Vermont/Caledonia_SaintJohnsbury_rev.geoJSON',
    'data/State_of_Vermont/Franklin_Fairfield_rev02012020.geojson'
]

for fpath in files_to_check:
    path = Path(fpath)
    if not path.exists():
        print(f'✗ {path.name}: FILE NOT FOUND')
        continue
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if not data['features']:
        print(f'✗ {path.name}: NO FEATURES')
        continue
    
    props = data['features'][0]['properties']
    print(f'\n=== {path.name} ===')
    print(f'Total properties: {len(props)}')
    print(f'Total features: {len(data["features"])}')
    
    # Check for expected fields
    missing = []
    found = []
    for field in expected_fields:
        if field in props:
            found.append(field)
        else:
            missing.append(field)
    
    print(f'\nExpected fields: {len(expected_fields)}')
    print(f'  Found: {len(found)}')
    print(f'  Missing: {len(missing)}')
    
    if missing:
        print(f'\n⚠ MISSING FIELDS:')
        for field in sorted(missing):
            print(f'  - {field}')
    
    print(f'\n✓ FOUND FIELDS:')
    for field in sorted(found):
        val = repr(props[field])[:50]
        print(f'  - {field}: {val}')
    
    if not found:
        print('  (No expected fields found)')
        print(f'\n  Actual properties:')
        for key in sorted(props.keys()):
            val = repr(props[key])[:50]
            print(f'    - {key}: {val}')
