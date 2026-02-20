import json

# Load original file
with open('data/State_of_Vermont/Addison_Addison_rev12262017.geojson', 'r') as f:
    original = json.load(f)

# Load transformed file
with open('data/temp/Addison_Addison_rev12262017.geojson', 'r') as f:
    transformed = json.load(f)

# Get sample feature properties
print('=== ORIGINAL FILE ===')
print(f'Type: {original["type"]}')
print(f'Features: {len(original["features"])}')
print(f'Sample feature properties (first 15 keys):')
orig_props = list(original['features'][0]['properties'].keys())[:15]
for prop in orig_props:
    print(f'  - {prop}')

print(f'\nTotal properties in sample: {len(original["features"][0]["properties"])}')

print('\n=== TRANSFORMED FILE ===')
print(f'Type: {transformed["type"]}')
print(f'Features: {len(transformed["features"])}')
print(f'Sample feature properties (first 15 keys):')
trans_props = list(transformed['features'][0]['properties'].keys())[:15]
for prop in trans_props:
    print(f'  - {prop}')

print(f'\nTotal properties in sample: {len(transformed["features"][0]["properties"])}')

# Compare properties
orig_set = set(original['features'][0]['properties'].keys())
trans_set = set(transformed['features'][0]['properties'].keys())

print('\n=== CHANGES ===')
print(f'Fields removed: {len(orig_set - trans_set)}')
print(f'Fields added/renamed: {len(trans_set - orig_set)}')

# Show some examples
removed = list(orig_set - trans_set)[:10]
added = list(trans_set - orig_set)[:10]

if removed:
    print(f'\nExample removed fields:')
    for f in removed:
        print(f'  - {f}')

if added:
    print(f'\nExample added fields (renamed):')
    for f in added:
        print(f'  - {f}')

# Verify data preservation
print('\n=== GEOMETRY & FEATURE VERIFICATION ===')
print(f'Features match: {len(original["features"]) == len(transformed["features"])}')
print(f'First feature geometry type: {original["features"][0]["geometry"]["type"]}')
print(f'Geometry preserved: {original["features"][0]["geometry"] == transformed["features"][0]["geometry"]}')

# Check a specific renamed field
print('\n=== SPECIFIC RENAME VERIFICATION ===')
if "1F Allowance" in original['features'][0]['properties']:
    orig_val = original['features'][0]['properties']['1F Allowance']
    if "F1F_Allowance" in transformed['features'][0]['properties']:
        trans_val = transformed['features'][0]['properties']['F1F_Allowance']
        print(f'1F Allowance: "{orig_val}" → F1F_Allowance: "{trans_val}"')
        print(f'Value preserved: {orig_val == trans_val}')
    else:
        print('F1F_Allowance not found in transformed file')
else:
    print('1F Allowance field not in original')
