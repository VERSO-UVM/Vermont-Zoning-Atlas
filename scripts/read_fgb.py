import geopandas as gpd
import pandas as pd
from pathlib import Path

fgb_file = Path('vt-zoning-update.fgb')

try:
    # Read the FGB file
    gdf = gpd.read_file(fgb_file)
    
    print(f'=== VT-ZONING-UPDATE.FGB ===\n')
    print(f'Total features: {len(gdf)}')
    print(f'CRS: {gdf.crs}')
    print(f'Columns: {len(gdf.columns)}')
    print(f'Column names: {list(gdf.columns)}\n')
    
    # Test worst-off jurisdictions
    worst_off_juris = [
        'Glastenbury', 'Peru', 'Sunderland', 'Woodford', 
        'Barnet', 'SaintJohnsbury', 'Stannard', 'Sutton', 'Waterford',
        'Averill', 'Brighton', 'Brunswick', 'Canaan', 'Concord',
        'Berlin', 'Cabot', 'Calais', 'Duxbury', 'EastMontpelier',
        'Dover', 'Dummerston', 'Marlboro', 'Stratton', 'Wardsboro'
    ]
    
    print('=== CHECKING WORST-OFF JURISDICTIONS ===\n')
    
    # FGB uses spaces in column names, not underscores
    for juris in worst_off_juris[:10]:  # Check first 10
        # Search for this jurisdiction
        matches = gdf[gdf['Jurisdiction District Name'].str.contains(juris, case=False, na=False)]
        
        if len(matches) > 0:
            props = matches.iloc[0]
            prop_count = len([c for c in gdf.columns if props[c] is not None])
            
            # Check specific zoning fields - also with spaces
            has_f1f = '1F Allowance' in gdf.columns and pd.notna(matches.iloc[0]['1F Allowance'])
            
            status = '✓ GOOD' if has_f1f else '⚠ LIMITED'
            print(f'{juris}: {len(matches)} features, {status}')
            if has_f1f:
                print(f'  1F Allowance: {matches.iloc[0]["1F Allowance"]}')
                print(f'  Non-null properties: {prop_count}')
        else:
            print(f'{juris}: NOT FOUND')
    
except Exception as e:
    print(f'Error reading FGB file: {e}')
    print(f'\nTrying alternative approach...')
    
    # Try with ogr2ogr or fiona
    import subprocess
    result = subprocess.run(['ogrinfo', str(fgb_file)], capture_output=True, text=True)
    print(result.stdout)
