import geopandas as gpd

# Read the GeoJSON file
gdf = gpd.read_file("data/vt-zoning-expanded-vermont.geojson")

# Get all unique fields
unique_fields = gdf.columns

# Count non-empty values for each field
field_counts = {field: gdf[field].count() for field in unique_fields}

# Sort the fields by count (lowest values first)
sorted_field_counts = sorted(field_counts.items(), key=lambda x: x[1])

# Print the sorted field counts
for field, count in sorted_field_counts:
    print(f"{field}: {count}")
