import json
from pathlib import Path

# List of 125 files with 3 properties (worst off)
worst_off_files = [
    'Bennington_Glastenbury_rev.geoJSON',
    'Bennington_Peru_rev.geoJSON',
    'Bennington_Sunderland_Overlay_rev.geoJSON',
    'Bennington_Sunderland_rev.geoJSON',
    'Bennington_Woodford_Overlay_rev.geoJSON',
    'Bennington_Woodford_rev.geoJSON',
    'Caledonia_Barnet_rev.geoJSON',
    'Caledonia_Burke_rev.geoJSON',
    'Caledonia_Danville_rev.geoJSON',
    'Caledonia_Groton_rev.geoJSON',
    'Caledonia_Hardwick_rev.geoJSON',
    'Caledonia_Kirby_rev.geoJSON',
    'Caledonia_Lyndon_rev.geoJSON',
    'Caledonia_Peacham_rev.geoJSON',
    'Caledonia_Ryegate_rev.geoJSON',
    'Caledonia_SaintJohnsbury_rev.geoJSON',
    'Caledonia_Stannard_rev.geoJSON',
    'Caledonia_Sutton_rev.geoJSON',
    'Caledonia_Waterford_rev.geoJSON',
    'Essex_Averill_rev.geoJSON',
    'Essex_AverysGore_rev.geoJSON',
    'Essex_Brighton_rev.geoJSON',
    'Essex_Brunswick_rev.geoJSON',
    'Essex_Canaan_Overlay_rev.geoJSON',
    'Essex_Canaan_rev.geoJSON',
    'Essex_Concord_rev.geoJSON',
    'Essex_Ferdinand_rev.geoJSON',
    'Essex_Granby_rev.geoJSON',
    'Essex_Guildhall_rev.geoJSON',
    'Essex_Lemington_rev.geoJSON',
    'Essex_Lewis_rev.geoJSON',
    'Essex_Maidstone_Overlay_rev.geoJSON',
    'Essex_Maidstone_rev.geoJSON',
    'Essex_Norton_Overlay_rev.geoJSON',
    'Essex_Norton_rev.geoJSON',
    'Essex_WarnersGrant_rev.geoJSON',
    'Essex_WarrensGore_rev.geoJSON',
    'Orange_BradfordTown_Overlay_rev.geoJSON',
    'Orange_BradfordTown_rev.geoJSON',
    'Orange_Braintree_Overlay_rev.geoJSON',
    'Orange_Braintree_rev.geoJSON',
    'Orange_Brookfield_Overlay_rev.geoJSON',
    'Orange_Brookfield_rev.geoJSON',
    'Orange_Chelsea_Overlay_rev.geoJSON',
    'Orange_Chelsea_rev.geoJSON',
    'Orange_Newbury_rev.geoJSON',
    'Orange_Randolph_Overlay_rev.geoJSON',
    'Orange_Strafford_Overlay_rev.geoJSON',
    'Orange_Strafford_rev.geoJSON',
    'Orange_Thetford_Overlay_rev.geoJSON',
    'Orange_Thetford_rev.geoJSON',
    'Orange_Vershire_Overlay_rev.geoJSON',
    'Orange_Vershire_rev.geoJSON',
    'Orange_Washington_rev.geoJSON',
    'Orleans_Barton_rev.geoJSON',
    'Orleans_Greensboro_rev.geoJSON',
    'Orleans_Jay_rev.geoJSON',
    'Orleans_Lowell_rev.geoJSON',
    'Orleans_Morgan_rev.geoJSON',
    'Orleans_NewportCity_FBCOoverlay_rev.geoJSON',
    'Orleans_NewportCity_rev.geoJSON',
    'Orleans_NewportTown_rev.geoJSON',
    'Orleans_Troy_Overlay_rev.geoJSON',
    'Orleans_Westmore_rev.geoJSON',
    'Washington_BarreCity_Overlay_rev.geoJSON',
    'Washington_BarreCity_rev.geoJSON',
    'Washington_Berlin_rev.geoJSON',
    'Washington_Cabot_rev.geoJSON',
    'Washington_Calais_Overlay_rev.geoJSON',
    'Washington_Calais_Overlays_rev.geoJSON',
    'Washington_Calais_rev.geoJSON',
    'Washington_Duxbury_Overlay_rev.geoJSON',
    'Washington_Duxbury_rev.geoJSON',
    'Washington_EastMontpelier_rev.geoJSON',
    'Washington_Fayston_Overlay_rev.geoJSON',
    'Washington_Fayston_rev.geoJSON',
    'Washington_Marshfield_rev.geoJSON',
    'Washington_Middlesex_Overlay_rev.geoJSON',
    'Washington_Middlesex_rev.geoJSON',
    'Washington_Montpelier_rev.geoJSON',
    'Washington_Moretown_Overlay_rev.geoJSON',
    'Washington_Moretown_rev.geoJSON',
    'Washington_Plainfield_rev.geoJSON',
    'Washington_Waitsfield_ARO_rev.geoJSON',
    'Washington_Waitsfield_FEHO_rev.geoJSON',
    'Washington_Waitsfield_FHO_rev.geoJSON',
    'Washington_Waitsfield_HCVO_rev.geoJSON',
    'Washington_Waitsfield_rev.geoJSON',
    'Washington_Warren_Flood_rev.geoJSON',
    'Washington_Warren_Meadow_rev.geoJSON',
    'Washington_Warren_rev.geoJSON',
    'Washington_Woodbury_rev.geoJSON',
    'Windham_Dover_rev.geoJSON',
    'Windham_Dummerston_rev.geoJSON',
    'Windham_Marlboro_rev.geoJSON',
    'Windham_Stratton_rev.geoJSON',
    'Windham_Wardsboro_rev.geoJSON',
    'Windham_Westminster_rev.geoJSON',
    'Windham_Whitingham_rev.geoJSON',
    'Windham_Wilmington_rev.geoJSON',
    'Windham_Windham_rev.geoJSON',
    'Windsor_Barnard_Overlay_rev.geoJSON',
    'Windsor_Barnard_rev.geoJSON',
    'Windsor_Bethel_Overlay_rev.geoJSON',
    'Windsor_Bethel_rev.geoJSON',
    'Windsor_Chester_Overlay_rev.geoJSON',
    'Windsor_Chester_rev.geoJSON',
    'Windsor_Hartford_Overlay_rev.geoJSON',
    'Windsor_Hartford_rev.geoJSON',
    'Windsor_Norwich_Overlay_rev.geoJSON',
    'Windsor_Plymouth_Overlay_rev.geoJSON',
    'Windsor_Plymouth_rev.geoJSON',
    'Windsor_Pomfret_Overlays_rev.geoJSON',
    'Windsor_Pomfret_rev.geoJSON',
    'Windsor_Reading_Overlays_rev.geoJSON',
    'Windsor_Reading_rev.geoJSON',
    'Windsor_Rochester_rev.geoJSON',
    'Windsor_Stockbridge_Overlay_rev.geoJSON',
    'Windsor_Weathersfield_rev.geoJSON',
    'Windsor_WestWindsor_rev.geoJSON',
    'Windsor_Windsor_Overlay_rev.geoJSON',
    'Windsor_Windsor_rev.geoJSON',
    'Windsor_WoodstockTown_Overlays_rev.geoJSON',
    'Windsor_WoodstockTown_rev.geoJSON',
    'Windsor_WoodstockVillage_Overlay_rev.geoJSON',
]

current_dir = Path('data/State_of_Vermont')
archive_dir = Path('data/State_of_Vermont_archive')

print(f'=== COMPARING {len(worst_off_files)} WORST-OFF FILES ===\n')

different_count = 0
same_count = 0
missing_in_archive = 0
missing_in_current = 0

for fname in worst_off_files:
    curr_path = current_dir / fname
    arch_path = archive_dir / fname
    
    if not curr_path.exists():
        print(f'✗ {fname}: MISSING IN CURRENT')
        missing_in_current += 1
        continue
    
    if not arch_path.exists():
        print(f'? {fname}: NOT IN ARCHIVE')
        missing_in_archive += 1
        continue
    
    # Load both files
    try:
        with open(curr_path) as f:
            curr_data = json.load(f)
        with open(arch_path) as f:
            arch_data = json.load(f)
        
        curr_props = len(curr_data['features'][0]['properties']) if curr_data['features'] else 0
        arch_props = len(arch_data['features'][0]['properties']) if arch_data['features'] else 0
        
        if curr_props == arch_props:
            same_count += 1
            if curr_props <= 3:
                print(f'✓ {fname}: SAME ({arch_props} → {curr_props} props)')
        else:
            different_count += 1
            print(f'⚠ {fname}: DIFFERENT (Archive: {arch_props} props → Current: {curr_props} props)')
    
    except Exception as e:
        print(f'✗ {fname}: ERROR - {e}')

print(f'\n=== SUMMARY ===')
print(f'Files checked: {len(worst_off_files)}')
print(f'  Same (no change): {same_count}')
print(f'  Different: {different_count}')
print(f'  Missing in archive: {missing_in_archive}')
print(f'  Missing in current: {missing_in_current}')

if different_count > 0:
    print(f'\n⚠️ {different_count} files changed! These may have gained data during transformation.')
else:
    print(f'\n✓ All worst-off files are UNCHANGED - limited data is original.')
