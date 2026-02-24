import json
from pathlib import Path
from collections import defaultdict

# List of worst-off jurisdictions (extracted from filenames)
worst_off_jurisdictions = [
    'Glastenbury', 'Peru', 'Sunderland', 'Woodford', 
    'Barnet', 'Burke', 'Danville', 'Groton', 'Hardwick', 'Kirby', 'Lyndon', 
    'Peacham', 'Ryegate', 'SaintJohnsbury', 'Stannard', 'Sutton', 'Waterford',
    'Averill', 'AverysGore', 'Brighton', 'Brunswick', 'Canaan', 'Concord', 
    'Ferdinand', 'Granby', 'Guildhall', 'Lemington', 'Lewis', 'Maidstone', 'Norton',
    'BradfordTown', 'Braintree', 'Brookfield', 'Chelsea', 'Newbury', 'Randolph', 
    'Strafford', 'Thetford', 'Vershire', 'Washington',
    'Barton', 'Greensboro', 'Jay', 'Lowell', 'Morgan', 'NewportCity', 'NewportTown',
    'Troy', 'Westmore',
    'Berlin', 'Cabot', 'Calais', 'Duxbury', 'EastMontpelier', 'Fayston',
    'Marshfield', 'Middlesex', 'Montpelier', 'Moretown', 'Plainfield', 'Waitsfield', 'Warren', 'Woodbury',
    'Dover', 'Dummerston', 'Marlboro', 'Stratton', 'Wardsboro', 'Westminster', 'Whitingham', 'Wilmington', 'Windham',
    'Barnard', 'Bethel', 'Chester', 'Hartford', 'Norwich', 'Plymouth', 'Pomfret', 'Reading', 'Rochester',
    'Stockbridge', 'Weathersfield', 'WestWindsor', 'Windsor', 'WoodstockTown', 'WoodstockVillage'
]

# Find RPC files
rpc_dir = Path('data/RPC')
rpc_files = list(rpc_dir.glob('*/*_Zoning.geojson'))

print(f'=== CHECKING WORST-OFF JURISDICTIONS IN RPC FILES ===\n')
print(f'Worst-off jurisdictions to find: {len(worst_off_jurisdictions)}')
print(f'RPC files found: {len(rpc_files)}\n')

found_by_rpc = defaultdict(list)
found_jurisdictions = set()

# Search in RPC files
for rpc_file in sorted(rpc_files):
    rpc_name = rpc_file.parent.name
    
    with open(rpc_file, encoding='utf-8') as f:
        data = json.load(f)
    
    for feature in data['features']:
        props = feature['properties']
        dist_name = props.get('Jurisdiction_District_Name', '')
        
        # Check if this matches any worst-off jurisdiction
        for jurisdiction in worst_off_jurisdictions:
            if jurisdiction in dist_name:
                prop_count = len(props)
                found_by_rpc[rpc_name].append({
                    'name': dist_name,
                    'properties': prop_count,
                    'file': rpc_file.name
                })
                found_jurisdictions.add(jurisdiction)
                break

# Report findings
for rpc_name in sorted(found_by_rpc.keys()):
    features = found_by_rpc[rpc_name]
    print(f'\n=== {rpc_name} ===')
    print(f'Features found: {len(features)}')
    
    # Group by property count
    by_props = defaultdict(list)
    for feat in features:
        by_props[feat['properties']].append(feat)
    
    for prop_count in sorted(by_props.keys()):
        feats = by_props[prop_count]
        print(f'\n  {prop_count} properties ({len(feats)} features):')
        for feat in sorted(feats, key=lambda x: x['name'])[:5]:  # Show first 5
            status = '✓ GOOD' if prop_count >= 50 else '⚠ LIMITED'
            print(f'    - {feat["name"]}: {status}')
        if len(feats) > 5:
            print(f'    ... and {len(feats) - 5} more')

print(f'\n=== SUMMARY ===')
print(f'Unique worst-off jurisdictions found in RPC: {len(found_jurisdictions)}/{len(worst_off_jurisdictions)}')
print(f'Total features found: {sum(len(v) for v in found_by_rpc.values())}')

# Identify those with sufficient data
good_count = 0
limited_count = 0
for rpc_features in found_by_rpc.values():
    for feat in rpc_features:
        if feat['properties'] >= 50:
            good_count += 1
        else:
            limited_count += 1

print(f'\n✓ Features with ≥50 properties (GOOD): {good_count}')
print(f'⚠ Features with <50 properties (LIMITED): {limited_count}')

if limited_count > 0:
    print(f'\n⚠️ Many worst-off jurisdictions still have limited data in RPC files!')
else:
    print(f'\n✓ All worst-off jurisdictions have complete data in RPC files!')
