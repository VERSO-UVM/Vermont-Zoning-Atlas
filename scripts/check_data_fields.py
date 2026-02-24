import json
from pathlib import Path

# Check for Fairfield and Saint Johnsbury files
data_dir = Path('data/State_of_Vermont')
files_found = []

for f in data_dir.glob('*Fairfield*'):
    files_found.append(f.name)
for f in data_dir.glob('*SaintJohnsbury*'):
    files_found.append(f.name)

print('Files found:')
for f in sorted(files_found):
    print(f'  - {f}')

# Check each file
for fname in sorted(files_found):
    fpath = data_dir / fname
    with open(fpath, 'r') as f:
        data = json.load(f)
    
    print(f'\n=== {fname} ===')
    print(f'Features: {len(data["features"])}')
    if data['features']:
        props = data['features'][0]['properties']
        print(f'Sample properties: {len(props)} total')
        
        # Check for key fields
        has_f1f = 'F1F_Allowance' in props
        print(f'F1F_Allowance present: {"✓" if has_f1f else "✗"}')
        
        if has_f1f:
            val = props['F1F_Allowance']
            print(f'  Value: {repr(val)}')
        
        # Show first feature details
        dist_name = props.get('Jurisdiction_District_Name', 'N/A')
        overlay = props.get('Overlay_District', 'N/A')
        county = props.get('County', 'N/A')
        
        print(f'First feature: {dist_name} (County: {county}, Overlay: {overlay})')
        
        # List all Allowance fields
        allowance_fields = [k for k in props.keys() if 'Allowance' in k]
        if allowance_fields:
            print(f'  Allowance fields: {", ".join(sorted(allowance_fields))}')
