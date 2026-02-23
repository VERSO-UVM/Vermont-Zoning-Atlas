import geopandas as gpd
from pathlib import Path
import json
from datetime import datetime

state_vt_dir = Path('data/State_of_Vermont')
fgb_gdf = gpd.read_file(Path('data/temp/vt-zoning-update_standardized.geojson'))

print(f"=== FGB DATA RECOVERY ANALYSIS ===")
print(f"Started: {datetime.now().strftime('%H:%M:%S')}\n")

# Get all files
all_files = sorted(list(state_vt_dir.glob('*.geojson')) + list(state_vt_dir.glob('*.geoJSON')))
print(f"Scanning {len(all_files)} files...\n")

recoverable = []
not_found = []
same_data = []
errors = []

for i, file_path in enumerate(all_files):
    if (i + 1) % 50 == 0:
        print(f"Progress: {i + 1}/{len(all_files)}")
    
    file_base = file_path.name
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
                recoverable.append({
                    'file': file_base,
                    'current': int(current_props),
                    'fgb': int(fgb_props),
                    'gain': int(gain),
                    'district': matches.iloc[0].get('District_Name', '')
                })
            else:
                same_data.append(file_base)
        else:
            not_found.append(file_base)
    
    except Exception as e:
        errors.append((file_base, str(e)))

print(f"\n=== RESULTS ===")
print(f"Recoverable: {len(recoverable)}/{len(all_files)}")
print(f"Not in FGB: {len(not_found)}/{len(all_files)}")
print(f"Same data: {len(same_data)}/{len(all_files)}")
print(f"Errors: {len(errors)}/{len(all_files)}")

if recoverable:
    total_gain = sum(r['gain'] for r in recoverable)
    print(f"\n=== RECOVERY POTENTIAL ===")
    print(f"Total properties recoverable: {total_gain:,}")
    print(f"Average per file: {total_gain / len(recoverable):.1f}")
    print(f"Max per file: {max(r['gain'] for r in recoverable)}")
    
    print(f"\n=== TOP 15 RECOVERABLE FILES ===")
    for r in sorted(recoverable, key=lambda x: x['gain'], reverse=True)[:15]:
        print(f"{r['file']}: +{r['gain']} ({r['current']} → {r['fgb']})")

# Save full results
results_dir = Path('analysis/fgb_comparison')
results_dir.mkdir(exist_ok=True)

results = {
    'timestamp': datetime.now().isoformat(),
    'summary': {
        'total_files': len(all_files),
        'recoverable': len(recoverable),
        'not_in_fgb': len(not_found),
        'same_data': len(same_data),
        'errors': len(errors),
        'total_recovery_properties': int(sum(r['gain'] for r in recoverable)) if recoverable else 0
    },
    'recoverable_details': recoverable,
    'not_found_files': not_found[:50],  # First 50 to avoid huge JSON
    'same_data_files': same_data[:50]
}

with open(results_dir / 'fgb_recovery_full.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to: analysis/fgb_comparison/fgb_recovery_full.json")
print(f"Completed: {datetime.now().strftime('%H:%M:%S')}")
