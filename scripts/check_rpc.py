import json
from pathlib import Path

# Check the RPC merged file for Saint Johnsbury
rpc_file = Path('data/RPC/NVDA/NVDA_Zoning.geojson')

if rpc_file.exists():
    with open(rpc_file, 'r') as f:
        data = json.load(f)
    
    print(f'Checking {rpc_file.name}')
    print(f'Total features: {len(data["features"])}')
    
    # Find Saint Johnsbury features
    sj_features = [feat for feat in data['features'] if 'Saint Johnsbury' in feat['properties'].get('Jurisdiction_District_Name', '')]
    
    print(f'\nSaint Johnsbury features found in RPC: {len(sj_features)}')
    if sj_features:
        props = sj_features[0]['properties']
        print(f'Properties in RPC version: {len(props)} total')
        
        has_f1f = 'F1F_Allowance' in props
        print(f'F1F_Allowance: {has_f1f}')
        if has_f1f:
            print(f'  Value: {repr(props["F1F_Allowance"])}')
        
        print(f'First feature district: {props.get("Jurisdiction_District_Name")}')
        
        # Show some properties
        print(f'\nSample properties:')
        for key in sorted(list(props.keys())[:10]):
            print(f'  - {key}')
