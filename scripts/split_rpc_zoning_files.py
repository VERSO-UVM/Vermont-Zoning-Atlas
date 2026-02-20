#!/usr/bin/env python3
r"""
Split RPC zoning GeoJSON files into individual town files.

This script processes all RPC (Regional Planning Commission) zoning files from the
data\RPC directory and splits them into individual town files following the naming
convention used in data\State_of_Vermont (County_Town_rev.geojson).

The split town files are saved to data\Temp_town_files for review before moving
to the main State_of_Vermont directory.
"""

import json
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime


def split_rpc_files(rpc_base_path, output_path):
    """
    Split all RPC zoning files into individual town files.
    
    Args:
        rpc_base_path (str): Path to the RPC directory containing subdirectories
        output_path (str): Path where individual town files will be saved
    """
    
    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    
    # Get all RPC subdirectories
    rpc_dirs = [d for d in os.listdir(rpc_base_path) 
                if os.path.isdir(os.path.join(rpc_base_path, d)) 
                and d not in ['__pycache__']]
    
    rpc_dirs.sort()
    
    total_towns = 0
    processed_files = 0
    
    print("="*80)
    print("RPC ZONING FILES SPLITTER")
    print("="*80)
    print(f"\nProcessing RPC directories from: {rpc_base_path}")
    print(f"Output directory: {output_path}\n")
    
    for rpc_dir in rpc_dirs:
        rpc_dir_path = os.path.join(rpc_base_path, rpc_dir)
        
        # Find all _Zoning.geojson files in this directory
        zoning_files = [f for f in os.listdir(rpc_dir_path) 
                       if f.endswith('_Zoning.geojson')]
        
        if not zoning_files:
            continue
        
        for zoning_file in zoning_files:
            zoning_path = os.path.join(rpc_dir_path, zoning_file)
            processed_files += 1
            
            print(f"Processing: {rpc_dir}/{zoning_file}")
            
            try:
                # Read the RPC zoning file
                with open(zoning_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Group features by jurisdiction and county
                town_features = defaultdict(list)
                
                for feature in data.get('features', []):
                    props = feature.get('properties', {})
                    
                    # Extract jurisdiction and county
                    jurisdiction = props.get('Jurisdiction', '').strip()
                    county = props.get('County', '').strip()
                    
                    if jurisdiction and county:
                        # Use county_town as key
                        key = (county, jurisdiction)
                        town_features[key].append(feature)
                
                # Create individual town files
                for (county, jurisdiction), features in sorted(town_features.items()):
                    # Create filename following convention: County_Town_rev.geojson
                    # Clean up names (remove extra spaces, handle special cases)
                    county_clean = county.replace(' ', '').strip()
                    town_clean = jurisdiction.replace(' ', '').strip()
                    
                    filename = f"{county_clean}_{town_clean}_rev.geojson"
                    filepath = os.path.join(output_path, filename)
                    
                    # Create GeoJSON structure
                    geojson_output = {
                        "type": "FeatureCollection",
                        "features": features
                    }
                    
                    # Write to file
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(geojson_output, f, indent=2)
                    
                    print(f"  -> Created: {filename} ({len(features)} features)")
                    total_towns += 1
                
            except json.JSONDecodeError as e:
                print(f"  ERROR: Invalid JSON in {zoning_file}: {e}")
            except Exception as e:
                print(f"  ERROR: {e}")
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Processed RPC files: {processed_files}")
    print(f"Town files created: {total_towns}")
    
    # List created files
    if total_towns > 0:
        print(f"\nTown files saved to: {output_path}")
        print("\nCreated files:")
        created_files = sorted(os.listdir(output_path))
        for f in created_files:
            filepath = os.path.join(output_path, f)
            file_size = os.path.getsize(filepath)
            print(f"  - {f} ({file_size:,} bytes)")


def main():
    """Main execution function."""
    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    rpc_base_path = os.path.join(script_dir, 'data', 'RPC')
    output_path = os.path.join(script_dir, 'data', 'Temp_town_files')
    
    # Check if RPC directory exists
    if not os.path.exists(rpc_base_path):
        print(f"ERROR: RPC directory not found: {rpc_base_path}")
        return
    
    # Split the files
    split_rpc_files(rpc_base_path, output_path)
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
