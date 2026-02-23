import json
from pathlib import Path

# Check archive version
archive_dir = Path('data/State_of_Vermont_archive')
fpath = archive_dir / 'Caledonia_SaintJohnsbury_rev.geoJSON'

if fpath.exists():
    with open(fpath, 'r') as f:
        data = json.load(f)
    
    print(f'Archive version: {fpath.name}')
    print(f'Features: {len(data["features"])}')
    if data['features']:
        props = data['features'][0]['properties']
        print(f'Properties: {len(props)} total')
        print(f'F1F_Allowance in archive: {"F1F_Allowance" in props}')
        
        # Check for abbreviated field
        f1f_abbrev = [k for k in props.keys() if 'F1F' in k or 'ALLOWED' in k or 'Allowed' in k]
        print(f'\nFields with F1F or Allowed:')
        for name in sorted(f1f_abbrev)[:5]:
            print(f'  - {name}: {repr(props[name])[:50]}')
        
        print(f'\nAll properties (first 30):')
        for name in sorted(props.keys())[:30]:
            val = repr(props[name])[:40]
            print(f'  - {name}: {val}')
else:
    print('Archive file not found')
    print(f'Looking in: {archive_dir}')
    if archive_dir.exists():
        files = list(archive_dir.glob('*Saint*'))
        print(f'Saint* files found: {[f.name for f in files]}')
