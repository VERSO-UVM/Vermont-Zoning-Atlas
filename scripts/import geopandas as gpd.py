import geopandas as gpd

# Read the GeoJSON file
gdf = gpd.read_file("data/vt-zoning-expanded-vermont.geojson")

# Get unique values of the 'RPC' field
unique_rpc_values = gdf['RPC'].unique()

# Split the data by 'RPC' field and save to separate files
for rpc_value in unique_rpc_values:
    rpc_gdf = gdf[gdf['RPC'] == rpc_value]
    rpc_gdf.to_file(f"data/vt-zoning-expanded-{rpc_value}.geojson", driver="GeoJSON")

print("GeoJSON file has been split into multiple files by the 'RPC'") 