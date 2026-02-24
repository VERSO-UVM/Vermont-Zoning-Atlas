import geopandas as gpd
from pathlib import Path
import json

state_vt_dir = Path('data/State_of_Vermont')
fgb_gdf = gpd.read_file(Path('data/temp/vt-zoning-update_standardized.geojson'))

print("=== QUICK FGB RECOVERY ANALYSIS ===\n")

# Sample 30 worst-off files
test_files = [
    'Bennington_Glastenbury_rev.geoJSON',
    'Bennington_Peru_rev.geoJSON',
    'Bennington_Woodford_rev.geoJSON',
    'Bennington_Sunderland_rev.geoJSON',
    'Caledonia_Averill_rev.geoJSON',
    'Caledonia_Barnet_rev.geoJSON',
    'Caledonia_Burke_rev.geoJSON',
    'Caledonia_Peacham_rev.geoJSON',
    'Caledonia_StJohnsbury_rev.geoJSON',
    'Essex_Averill_rev.geoJSON',
    'Essex_Canaan_rev.geoJSON',
    'Essex_Guildhall_rev.geoJSON',
    'Essex_Maidstone_rev.geoJSON',
    'Essex_Nolton_rev.geoJSON',
    'Orange_Arransburg_rev.geoJSON',
    'Orange_Bradford_rev.geoJSON',
    'Orange_Brookfield_rev.geoJSON',
    'Orange_Chelsea_rev.geoJSON',
    'Orange_Corinth_rev.geoJSON',
    'Orleans_Barton_rev.geoJSON',
    'Orleans_Brownington_rev.geoJSON',
    'Orleans_Craftsbury_rev.geoJSON',
    'Orleans_Greensboro_rev.geoJSON',
    'Orleans_Groton_rev.geoJSON',
    'Orleans_Hardwick_rev.geoJSON',
    'Orleans_Irasburg_rev.geoJSON',
    'Orleans_Lowell_rev.geoJSON',
    'Orleans_Lyndon_rev.geoJSON',
    'Orleans_Newark_rev.geoJSON',
    'Orleans_Newport_rev.geoJSON',
]

recoverable = []
not_found = []
same_data = []

for file_base in test_files:
    file_path = state_vt_dir / file_base
    if not file_path.exists():
        continue
    
    try:
        current_gdf = gpd.read_file(file_path)
        if len(current_gdf) == 0:
            continue
        
        current_props = current_gdf.iloc[0].count()
        
        # Parse filename
        base = file_base.replace('.geojson', '').replace('.geoJSON', '')
        parts = base.split('_')
        if len(parts) < 2:
            continue
        
        county = parts[0]
        town = parts[1].replace('_rev', '')
        
        # Search FGB
        matches = fgb_gdf[
            (fgb_gdf['District_Name'].str.contains(town, case=False, na=False)) &
            (fgb_gdf['County'].str.contains(county, case=False, na=False))
        ]
        
        if len(matches) > 0:
            fgb_props = matches.iloc[0].count()
            if fgb_props > current_props:
                gain = fgb_props - current_props
                recoverable.append((file_base, current_props, fgb_props, gain))
                print(f"✓ RECOVERABLE: {file_base}")
                print(f"   {current_props} → {fgb_props} (+{gain})")
            else:
                same_data.append(file_base)
                print(f"⚠ SAME: {file_base} ({current_props} props)")
        else:
            not_found.append(file_base)
            print(f"✗ NOT IN FGB: {file_base}")
    
    except Exception as e:
        print(f"✗ ERROR: {file_base}: {e}")

# Summary
print(f"\n=== SUMMARY ===")
print(f"Recoverable: {len(recoverable)}/{len(test_files)}")
print(f"Not in FGB: {len(not_found)}/{len(test_files)}")
print(f"Same data: {len(same_data)}/{len(test_files)}")

if recoverable:
    total_gain = sum(r[3] for r in recoverable)
    print(f"\nTotal properties recoverable: {total_gain}")
    print(f"Average per file: {total_gain / len(recoverable):.1f}")
