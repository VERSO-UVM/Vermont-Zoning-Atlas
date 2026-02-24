import json
from pathlib import Path
from collections import Counter

data_dir = Path('data/State_of_Vermont')
results = []

# Process all geojson files
for fpath in sorted(data_dir.glob('*.*json')):
    try:
        with open(fpath, 'r') as f:
            data = json.load(f)
        
        if not data.get('features'):
            results.append({
                'file': fpath.name,
                'properties': 0,
                'features': 0,
                'status': 'NO_FEATURES'
            })
            continue
        
        prop_count = len(data['features'][0]['properties'])
        feature_count = len(data['features'])
        
        results.append({
            'file': fpath.name,
            'properties': prop_count,
            'features': feature_count,
            'status': 'OK' if prop_count >= 50 else 'LIMITED'
        })
    
    except Exception as e:
        results.append({
            'file': fpath.name,
            'properties': 0,
            'features': 0,
            'status': f'ERROR: {e}'
        })

# Analysis
print('=== PROPERTIES ANALYSIS ===\n')

# Count by property ranges
property_counts = Counter(r['properties'] for r in results)
print('Distribution of property counts:')
for count in sorted(property_counts.keys()):
    print(f'  {count} properties: {property_counts[count]} files')

print(f'\nTotal files analyzed: {len(results)}')

# Find limited files
limited = [r for r in results if r['status'] == 'LIMITED']
print(f'\nFiles with LIMITED properties (< 50):')
print(f'  Count: {len(limited)} files')

if limited:
    print(f'\n  Property distribution:')
    limited_counts = Counter(r['properties'] for r in limited)
    for count in sorted(limited_counts.keys()):
        files = [r['file'] for r in limited if r['properties'] == count]
        print(f'\n    {count} properties ({limited_counts[count]} files):')
        for fname in sorted(files):
            print(f'      - {fname}')

# Show complete files
print(f'\n=== SUMMARY ===')
complete = [r for r in results if r['properties'] >= 50]
print(f'Complete files (≥ 50 properties): {len(complete)}')
print(f'Limited files (< 50 properties): {len(limited)}')
print(f'Error/Empty: {len([r for r in results if r["status"] not in ("OK", "LIMITED")])}')

# Show top property count
max_props = max(r['properties'] for r in results)
min_props = min(r['properties'] for r in results)
print(f'\nProperty count range: {min_props} - {max_props}')
