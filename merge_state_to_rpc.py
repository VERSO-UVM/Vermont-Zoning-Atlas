#!/usr/bin/env python3
r"""
Merge State_of_Vermont town files back into RPC regional files (v2).

This script consolidates individual town zoning files (State_of_Vermont)
back into their original RPC (Regional Planning Commission) groupings.
It handles files with both old and new schema formats by using county/jurisdiction
mapping for RPC identification.

Each RPC subdirectory will contain a single merged GeoJSON file.
"""

import json
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime


# County to RPC mapping (based on Vermont RPC regions)
COUNTY_TO_RPC = {
    'Addison': 'ACRPC',           # Addison County Regional Commission
    'Bennington': 'BCRC',          # Bennington County Regional Commission
    'Caledonia': 'NVDA',           # Northeast Kingdom (includes Essex/Orleans/Caledonia)
    'Chittenden': 'CCRPC',         # Chittenden County Regional Commission
    'Essex': 'RRPC',               # Rutland Regional Planning Commission (or NVDA)
    'Franklin': 'NWRPC',           # Northwest Regional Planning Commission
    'Grand Isle': 'NWRPC',         # Northwest Regional Planning Commission
    'Lamoille': 'LCPC',            # Lamoille County Planning Commission
    'Orange': 'RRPC',              # Rutland Regional Planning Commission
    'Orleans': 'NVDA',             # Northeast Kingdom
    'Rutland': 'RRPC',             # Rutland Regional Planning Commission
    'Washington': 'CCRPC',         # Central Vermont (Chittenden/Washington)
    'Windham': 'TRORC',            # Two Rivers-Ottauquechee Regional Commission
    'Windsor': 'RRPC',             # Rutland Regional Planning Commission
}

# Alternative jurisdiction-based mapping for edge cases
JURISDICTION_TO_RPC = {
    'Readsboro': 'WRC',            # Windham Regional Commission
    'Winhall': 'WRC',              # Windham Regional Commission
    'Northfield': 'CCRPC',         # Washington County to Chittenden area
}


def get_rpc_for_feature(feature, county_from_filename=None):
    """Extract or infer RPC from a feature's properties."""
    props = feature.get('properties', {})
    
    # First, try direct RPC field
    if 'RPC' in props:
        return props['RPC']
    
    # Then try jurisdiction-based mapping (for edge cases)
    jurisdiction = props.get('Jurisdiction', '')
    if jurisdiction in JURISDICTION_TO_RPC:
        return JURISDICTION_TO_RPC[jurisdiction]
    
    # Try county from properties
    county = props.get('County', '')
    if county and county in COUNTY_TO_RPC:
        return COUNTY_TO_RPC[county]
    
    # Fall back to county from filename
    if county_from_filename and county_from_filename in COUNTY_TO_RPC:
        return COUNTY_TO_RPC[county_from_filename]
    
    return None


def merge_state_to_rpc():
    """Merge State_of_Vermont files by RPC region and write to RPC directories."""
    
    state_dir = Path("data/State_of_Vermont")
    rpc_base_dir = Path("data/RPC")
    
    # Collect features by RPC
    rpc_features = defaultdict(list)
    rpc_towns = defaultdict(set)
    rpc_file_count = defaultdict(int)
    
    # Get all geojson files from State_of_Vermont
    state_files = sorted([f for f in state_dir.glob("*.geojson")])
    
    print("="*80)
    print("RPC MERGER - State_of_Vermont → RPC Regions (v2)")
    print("="*80)
    print(f"\nProcessing {len(state_files)} town files from State_of_Vermont...\n")
    
    total_features = 0
    files_processed = 0
    errors = []
    unmatched_rpcs = set()
    
    # Process each State_of_Vermont file
    for state_file in state_files:
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data.get('features'):
                print(f"⚠ {state_file.name:<50} No features")
                continue
            
            # Extract county from filename (e.g., "Addison_Addison_rev..." -> "Addison")
            filename_parts = state_file.stem.split('_')
            county_from_name = filename_parts[0] if filename_parts else None
            
            file_features = 0
            file_rpcs = set()
            
            # Process each feature and group by RPC
            for feature in data['features']:
                rpc = get_rpc_for_feature(feature, county_from_name)
                
                if rpc:
                    file_rpcs.add(rpc)
                    rpc_features[rpc].append(feature)
                    file_features += 1
                    total_features += 1
                    
                    # Track towns
                    county = feature['properties'].get('County', county_from_name)
                    jurisdiction = feature['properties'].get('Jurisdiction', 'Unknown')
                    for r in file_rpcs:
                        rpc_towns[r].add(f"{county}/{jurisdiction}")
                else:
                    unmatched_rpcs.add((state_file.name, county_from_name or '?'))
            
            if file_features > 0:
                rpc_str = ", ".join(sorted(file_rpcs))
                print(f"✓ {state_file.name:<50} {file_features:>6} features → {rpc_str}")
                files_processed += 1
                for rpc in file_rpcs:
                    rpc_file_count[rpc] += 1
            else:
                print(f"⚠ {state_file.name:<50} No RPC match")
        
        except json.JSONDecodeError as e:
            errors.append(f"{state_file.name}: Invalid JSON - {e}")
            print(f"✗ {state_file.name:<50} ERROR: Invalid JSON")
        except Exception as e:
            errors.append(f"{state_file.name}: {e}")
            print(f"✗ {state_file.name:<50} ERROR: {e}")
    
    print("\n" + "="*80)
    print("WRITING RPC MERGED FILES")
    print("="*80)
    
    # Get existing RPC subdirectories
    rpc_subdirs = sorted([d.name for d in rpc_base_dir.iterdir() if d.is_dir()])
    
    written_files = 0
    
    # Write merged files for each RPC
    for rpc in sorted(rpc_features.keys()):
        features = rpc_features[rpc]
        towns = rpc_towns[rpc]
        
        # Create merged FeatureCollection
        merged_geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        # Determine output path
        if rpc in rpc_subdirs:
            output_dir = rpc_base_dir / rpc
            output_file = output_dir / f"{rpc}_Zoning.geojson"
            
            # Write the merged file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(merged_geojson, f, indent=2, ensure_ascii=False)
            
            feature_count = len(features)
            town_count = len(towns)
            file_size_kb = output_file.stat().st_size / 1024
            town_files_count = rpc_file_count[rpc]
            
            print(f"\n✓ {rpc}")
            print(f"  File: {output_file.name}")
            print(f"  Features: {feature_count:,}")
            print(f"  Town files: {town_files_count}")
            print(f"  Unique towns: {town_count}")
            print(f"  Size: {file_size_kb:.1f} KB")
            
            written_files += 1
        else:
            print(f"\n⚠ {rpc}: No corresponding RPC subdirectory found")
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\nTotal State_of_Vermont files processed: {len(state_files)}")
    print(f"Files with RPC match: {files_processed}")
    print(f"Total features merged: {total_features:,}")
    print(f"RPC regions with features: {len(rpc_features)}")
    print(f"Merged files written: {written_files}")
    
    if unmatched_rpcs:
        print(f"\nWarnings: {len(unmatched_rpcs)} features with unmatched RPC")
        for file_name, county in list(unmatched_rpcs)[:5]:
            print(f"  - {file_name} (County: {county})")
        if len(unmatched_rpcs) > 5:
            print(f"  ... and {len(unmatched_rpcs) - 5} more")
    
    if errors:
        print(f"\nErrors encountered ({len(errors)}):")
        for error in errors[:5]:
            print(f"  - {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    merge_state_to_rpc()
