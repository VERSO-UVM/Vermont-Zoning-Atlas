#!/usr/bin/env python3
r"""
Pretty-print all GeoJSON files in State_of_Vermont directory.

This script converts minified GeoJSON files (all on one line) into pretty-printed
format with readable indentation for better human readability and easier debugging.
"""

import json
import os
from pathlib import Path
from datetime import datetime


def prettify_geojson_files(state_dir):
    """
    Convert all minified GeoJSON files to pretty-printed format.
    
    Args:
        state_dir (str): Path to the State_of_Vermont directory
    """
    
    geojson_files = [f for f in os.listdir(state_dir) 
                     if f.lower().endswith('.geojson')]
    geojson_files.sort()
    
    total_files = len(geojson_files)
    processed = 0
    bytes_saved = 0
    bytes_added = 0
    
    print("="*80)
    print("GEOJSON PRETTIFIER - State_of_Vermont")
    print("="*80)
    print(f"\nProcessing {total_files} GeoJSON files...\n")
    
    for filename in geojson_files:
        filepath = os.path.join(state_dir, filename)
        
        try:
            # Get original file size
            original_size = os.path.getsize(filepath)
            
            # Read and parse JSON
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Write back with pretty formatting
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Get new file size
            new_size = os.path.getsize(filepath)
            size_diff = new_size - original_size
            
            # Track statistics
            processed += 1
            if size_diff > 0:
                bytes_added += size_diff
            else:
                bytes_saved += abs(size_diff)
            
            # Show progress
            status = f"✓ {filename:<50}"
            original_kb = original_size / 1024
            new_kb = new_size / 1024
            size_info = f"{original_kb:>8.1f} KB → {new_kb:>8.1f} KB"
            
            if size_diff > 0:
                print(f"{status} {size_info} (+{size_diff / 1024:>6.1f} KB)")
            else:
                print(f"{status} {size_info} ({size_diff / 1024:>6.1f} KB)")
        
        except json.JSONDecodeError as e:
            print(f"✗ {filename:<50} ERROR: Invalid JSON - {e}")
        except Exception as e:
            print(f"✗ {filename:<50} ERROR: {e}")
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\nFiles processed: {processed}/{total_files}")
    print(f"Bytes added: {bytes_added / 1024:.1f} KB")
    print(f"Bytes saved: {bytes_saved / 1024:.1f} KB")
    print(f"\nAll files converted to pretty-printed format with 2-space indentation.")


def main():
    """Main execution function."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    state_dir = os.path.join(script_dir, 'data', 'State_of_Vermont')
    
    # Check if directory exists
    if not os.path.exists(state_dir):
        print(f"ERROR: State_of_Vermont directory not found: {state_dir}")
        return
    
    # Prettify the files
    prettify_geojson_files(state_dir)
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
