import geopandas as gpd
import pandas as pd
import json
from pathlib import Path
from collections import defaultdict

# Get all worst-off files from data/State_of_Vermont
state_vt_dir = Path('data/State_of_Vermont')
all_files = list(state_vt_dir.glob('*.geojson')) + list(state_vt_dir.glob('*.geoJSON'))

# Create a quick analysis first to find which files have only 3 properties
worst_off_files = []
print("=== ANALYZING STATE_OF_VERMONT FILES ===")
print(f"Total files to analyze: {len(all_files)}\n")

for geojson_file in sorted(all_files):
    try:
        gdf = gpd.read_file(geojson_file)
        if len(gdf) > 0:
            props = gdf.iloc[0].count()
            if props <= 5:  # Very minimal properties
                worst_off_files.append((geojson_file.name, props))
    except Exception as e:
        pass

# Show sample
print(f"Files with ≤5 properties: {len(worst_off_files)} files")
for fname, props in sorted(worst_off_files)[:20]:
    print(f"  {fname}: {props} properties")

results_dir = Path('analysis/fgb_comparison')
results_dir.mkdir(exist_ok=True)

print("=== COMPARING CURRENT VS FGB ZONING DATA ===\n")

# Load standardized FGB
print("Loading standardized FGB...")
fgb_gdf = gpd.read_file(Path('data/temp/vt-zoning-update_standardized.geojson'))
print(f"FGB: {len(fgb_gdf)} features, {len(fgb_gdf.columns)} columns\n")

comparison_results = []

for file_name, current_props in worst_off_files:
    geojson_path = state_vt_dir / file_name
    
    try:
        # Load current town file
        current_gdf = gpd.read_file(geojson_path)
        
        # Extract jurisdiction name from file path
        # E.g., "Addison_Orwell_rev03052019.geojson" -> county="Addison", town="Orwell"
        base = file_name.replace('.geojson', '').replace('.geoJSON', '')
        parts = base.split('_')
        
        if len(parts) >= 2:
            county = parts[0]
            town = parts[1]
            
            # Search FGB for matching jurisdiction
            fgb_matches = fgb_gdf[
                (fgb_gdf['District_Name'].str.contains(town, case=False, na=False)) &
                (fgb_gdf['County'].str.contains(county, case=False, na=False))
            ]
            
            if len(fgb_matches) > 0:
                fgb_row = fgb_matches.iloc[0]
                fgb_props = fgb_row.count()
                
                # Count zoning fields in FGB
                zoning_fields = [col for col in fgb_row.index if 'Allowance' in col and 'F' in col[:3]]
                zoning_populated = sum(1 for col in zoning_fields if pd.notna(fgb_row.get(col)))
                
                can_recover = fgb_props > current_props
                status = '✓ RECOVERED' if can_recover else '⚠ SAME'
                
                result = {
                    'town': file_name,
                    'county': county,
                    'current_props': current_props,
                    'fgb_props': fgb_props,
                    'fgb_matches': len(fgb_matches),
                    'zoning_fields': zoning_populated,
                    'can_recover': can_recover,
                    'status': status,
                    'fgb_district': fgb_row.get('District_Name', 'Unknown')
                }
                
                print(f"{status} {file_name}")
                print(f"   Current:  {current_props} properties")
                print(f"   FGB:      {fgb_props} properties ({fgb_props - current_props} additional)")
                print(f"   Zoning:   {zoning_populated}/{len(zoning_fields)} Allowance fields populated")
                print(f"   FGB District: {fgb_row.get('District_Name', 'Unknown')}")
                
                comparison_results.append(result)
            else:
                print(f"✗ NOT FOUND in FGB: {file_name} (searched for {county} / {town})")
        else:
            print(f"⚠ SKIP: {file_name} (cannot parse name)")
    
    except Exception as e:
        print(f"✗ ERROR {file_name}: {str(e)}")

# Summary
print("\n=== RECOVERY POTENTIAL ===")
can_recover = [r for r in comparison_results if r['can_recover']]
print(f"Files with recoverable data: {len(can_recover)}/{len(comparison_results)}")

total_props_gain = sum(r['fgb_props'] - r['current_props'] for r in can_recover)
print(f"Total properties that can be recovered: {total_props_gain}")

for result in sorted(can_recover, key=lambda x: x['fgb_props'] - x['current_props'], reverse=True)[:10]:
    gain = result['fgb_props'] - result['current_props']
    print(f"  {result['town']}: +{gain} properties ({result['current_props']} → {result['fgb_props']})")

# Save comparison results
json_results = []
for r in comparison_results:
    json_results.append({
        'town': r['town'],
        'county': r['county'],
        'current_properties': int(r['current_props']),
        'fgb_properties': int(r['fgb_props']),
        'properties_gain': int(r['fgb_props'] - r['current_props']),
        'fgb_matches': int(r['fgb_matches']),
        'zoning_fields_populated': int(r['zoning_fields']),
        'can_recover': bool(r['can_recover']),
        'status': r['status'],
        'fgb_district': r['fgb_district']
    })

with open(results_dir / 'fgb_comparison.json', 'w') as f:
    json.dump(json_results, f, indent=2)

print(f"\nResults saved to: {results_dir / 'fgb_comparison.json'}")
