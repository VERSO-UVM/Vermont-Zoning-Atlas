import json
from pathlib import Path

# Check archive
arch = Path('data/State_of_Vermont_archive/Caledonia_SaintJohnsbury_rev.geoJSON')
with open(arch) as f:
    arch_data = json.load(f)

print('Archive version:')
print(f'  Properties: {len(arch_data["features"][0]["properties"])}')
print(f'  Fields:', list(arch_data['features'][0]['properties'].keys()))

# Check RPC merged version
rpc = Path('data/RPC/NVDA/NVDA_Zoning.geojson')
with open(rpc) as f:
    rpc_data = json.load(f)

sj_rpc = [f for f in rpc_data['features'] if 'Saint Johnsbury' in f['properties'].get('Jurisdiction_District_Name', '')]
print(f'\nRPC version ({len(sj_rpc)} features):')
print(f'  Properties: {len(sj_rpc[0]["properties"])}')
print(f'  Fields:', list(sj_rpc[0]['properties'].keys()))
