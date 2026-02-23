import pandas as pd
import geopandas as gpd
import json
from pathlib import Path
from collections import defaultdict

# Read the CSV mapping file
csv_file = Path('analysis') / 'field_mapping_change.csv'
mapping_df = pd.read_csv(csv_file)

# Build mapping dictionaries
replace_mapping = {}  # old_name -> new_name
remove_fields = []    # fields to drop

for idx, row in mapping_df.iterrows():
    source = row['source_field']
    target = row['target_field']
    action = row['match_type']
    
    if action == 'Replace':
        if pd.notna(target):  # Has a target field
            replace_mapping[source] = target
    elif action == 'Remove':
        if pd.isna(target) or target == '':  # No target = remove
            remove_fields.append(source)

print(f"Replace Mapping: {len(replace_mapping)} fields")
print(f"Remove Mapping: {len(remove_fields)} fields")

# Apply to FGB file (convert to GeoJSON with standardized fields)
fgb_file = Path('vt-zoning-update.fgb')
output_dir = Path('data') / 'temp'
output_dir.mkdir(exist_ok=True)

print("\n=== Processing FGB file ===")
try:
    gdf = gpd.read_file(fgb_file)
    print(f"Loaded: {len(gdf)} features, {len(gdf.columns)} columns")
    
    # Rename columns
    rename_dict = {}
    for old_name in gdf.columns:
        if old_name in replace_mapping:
            rename_dict[old_name] = replace_mapping[old_name]
    
    # Apply rename
    gdf_renamed = gdf.rename(columns=rename_dict)
    
    # Remove columns marked for removal
    cols_to_drop = [col for col in remove_fields if col in gdf_renamed.columns]
    gdf_temp = gdf_renamed.drop(columns=cols_to_drop)
    
    # Remove ALL duplicates completely (don't keep any)
    duplicate_mask = gdf_temp.columns.duplicated(keep=False)
    if duplicate_mask.any():
        dup_names = gdf_temp.columns[duplicate_mask].unique()
        print(f"Found {len(dup_names)} duplicate column names (will remove all occurrences):")
        for name in list(dup_names)[:10]:
            print(f"  {name}")
        # Drop all duplicate columns
        gdf_clean = gdf_temp.loc[:, ~gdf_temp.columns.duplicated(keep=False)]
        print(f"Dropped all duplicates, kept {len(gdf_clean.columns)} unique columns")
    else:
        gdf_clean = gdf_temp
    
    print(f"After mapping: {len(gdf_clean.columns)} columns (all unique)")
    print(f"Renamed: {len(rename_dict)} fields")
    print(f"Removed: {len(cols_to_drop)} fields")
    
    # Save as GeoJSON
    output_file = output_dir / 'vt-zoning-update_standardized.geojson'
    gdf_clean.to_file(output_file, driver='GeoJSON')
    print(f"Saved: {output_file}")
    
    # Show sample of worst-off jurisdictions with standardized names
    print("\n=== Sample Data (Saint Johnsbury) ===")
    # Use the standardized column name
    juris_col = 'Jurisdiction_District_Name' if 'Jurisdiction_District_Name' in gdf_clean.columns else 'Jurisdiction District Name'
    
    if juris_col in gdf_clean.columns:
        sj = gdf_clean[gdf_clean[juris_col].str.contains('Saint Johnsbury', case=False, na=False)]
        if len(sj) > 0:
            print(f"Found {len(sj)} features")
            row = sj.iloc[0]
            non_null_count = row.count()
            print(f"Non-null properties: {non_null_count}")
            # Show first few properties
            props = row[row.notna()].head(10)
            for prop, val in props.items():
                print(f"  {prop}: {val}")
        else:
            print("Saint Johnsbury not found")
    else:
        print(f"Could not find jurisdiction column. Available columns: {list(gdf_clean.columns)[:10]}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
