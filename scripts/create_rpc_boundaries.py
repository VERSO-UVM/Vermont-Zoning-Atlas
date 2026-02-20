import json
import os

# RPC information
rpcs = {
    "ACRPC": {"name": "Addison County RPC", "municipalities": 23, "population": "37,000", "url": "http://www.acrpc.org/"},
    "BCRC": {"name": "Bennington County RPC", "municipalities": 19, "population": "36,000", "url": "http://www.bcrcvt.org/"},
    "CCRPC": {"name": "Chittenden County RPC", "municipalities": 19, "population": "168,000", "url": "http://www.ccrpcvt.org"},
    "CVRPC": {"name": "Central Vermont RPC", "municipalities": 23, "population": "59,000", "url": "http://www.centralvtplanning.org"},
    "LCPC": {"name": "Lamoille County PC", "municipalities": 13, "population": "26,000", "url": "http://www.lcpcvt.org"},
    "MARC": {"name": "Mount Ascutney RPC", "municipalities": 24, "population": "32,000", "url": "https://marcvt.org/"},
    "NVDA": {"name": "Northeastern Vermont Dev. Assoc.", "municipalities": 51, "population": "62,000", "url": "http://www.nvda.net"},
    "NWRPC": {"name": "Northwest RPC", "municipalities": 20, "population": "49,000", "url": "http://www.nrpcvt.com"},
    "RRPC": {"name": "Rutland RPC", "municipalities": 27, "population": "59,000", "url": "http://www.rutlandrpc.org"},
    "TRORC": {"name": "Two Rivers-Ottauquechee RPC", "municipalities": 30, "population": "47,000", "url": "http://www.trorc.org"},
    "WRC": {"name": "Windham RPC", "municipalities": 27, "population": "45,000", "url": "http://www.windhamregional.org"}
}

# Process each RPC's zoning file to extract geometries
features = []

try:
    import geopandas as gpd
    use_geopandas = True
    print("Using GeoPandas for geometry processing")
except:
    use_geopandas = False
    print("GeoPandas not available, using simple geometry extraction")

for abbrev, info in rpcs.items():
    rpc_file = f"data/RPC/{abbrev}/{abbrev}_Zoning.geojson"
    if os.path.exists(rpc_file):
        print(f"Processing {abbrev}...")
        try:
            if use_geopandas:
                # Use geopandas to dissolve all geometries into one
                gdf = gpd.read_file(rpc_file)
                dissolved = gdf.dissolve()
                geom_json = json.loads(dissolved.to_json())
                
                feature = geom_json['features'][0]
                feature['properties'] = {
                    "RPC_ABBREV": abbrev,
                    "RPC_NAME": info["name"],
                    "MUNICIPALITIES": info["municipalities"],
                    "POPULATION": info["population"],
                    "WEBSITE": info["url"]
                }
                features.append(feature)
            else:
                # Simple approach: collect all geometries
                with open(rpc_file, 'r') as f:
                    data = json.load(f)
                
                # Collect all polygons
                all_coords = []
                for feat in data['features']:
                    if feat['geometry']['type'] in ['Polygon', 'MultiPolygon']:
                        all_coords.append(feat['geometry'])
                
                if all_coords:
                    # Create a MultiPolygon or just use first geometry as placeholder
                    if len(all_coords) == 1:
                        geom = all_coords[0]
                    else:
                        geom = {
                            "type": "MultiPolygon",
                            "coordinates": [c['coordinates'] if c['type'] == 'Polygon' else c['coordinates'] for c in all_coords[:10]]  # Limit for size
                        }
                    
                    feature = {
                        "type": "Feature",
                        "properties": {
                            "RPC_ABBREV": abbrev,
                            "RPC_NAME": info["name"],
                            "MUNICIPALITIES": info["municipalities"],
                            "POPULATION": info["population"],
                            "WEBSITE": info["url"]
                        },
                        "geometry": geom
                    }
                    features.append(feature)
            
            print(f"  Added {abbrev}")
        except Exception as e:
            print(f"  Error processing {abbrev}: {e}")

if features:
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open('data/RPC_Boundaries.geojson', 'w') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"\nCreated RPC_Boundaries.geojson with {len(features)} features")
else:
    print("No features created")
