import json
import csv
import os
from pathlib import Path

# Read the field mapping CSV
mapping = {}
remove_fields = set()

with open('field_mapping_change.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        source = row['source_field'].strip()
        target = row['target_field'].strip()
        match_type = row['match_type'].strip()
        
        if match_type == 'Replace' and target:
            mapping[source] = target
        elif match_type == 'Remove':
            remove_fields.add(source)

print(f"Loaded {len(mapping)} field renames and {len(remove_fields)} field removals")

# Process all GeoJSON files in data/State_of_Vermont
state_dir = Path('data/State_of_Vermont')
temp_dir = Path('data/temp')

# Ensure temp directory exists
temp_dir.mkdir(parents=True, exist_ok=True)

geojson_files = list(state_dir.glob('*.geojson'))
print(f"Found {len(geojson_files)} GeoJSON files to process")

for geojson_file in geojson_files:
    try:
        # Read the GeoJSON file
        with open(geojson_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Process each feature
        for feature in data.get('features', []):
            if 'properties' in feature:
                props = feature['properties']
                
                # Apply field renames and removals
                keys_to_remove = []
                keys_to_rename = {}
                
                for current_key in list(props.keys()):
                    if current_key in remove_fields:
                        keys_to_remove.append(current_key)
                    elif current_key in mapping:
                        keys_to_rename[current_key] = mapping[current_key]
                
                # Remove fields
                for key in keys_to_remove:
                    del props[key]
                
                # Rename fields
                for old_name, new_name in keys_to_rename.items():
                    props[new_name] = props.pop(old_name)
        
        # Write to temp directory with same filename
        output_path = temp_dir / geojson_file.name
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Processed: {geojson_file.name}")
        
    except Exception as e:
        print(f"✗ Error processing {geojson_file.name}: {e}")

print("\nComplete! All files saved to data/temp/")
