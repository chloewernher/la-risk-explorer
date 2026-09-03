import json
from shapely.geometry import shape, mapping
from shapely.validation import make_valid
from shapely.ops import unary_union

NEIGHBORHOODS_PATH = "app/static/neighborhoods.geojson"
FIRE_PATH = "app/static/fire_events.geojson"
OUTPUT_PATH = "app/static/fire_events_clipped.geojson"

with open(NEIGHBORHOODS_PATH, "r") as f:
    neighborhoods = json.load(f)

with open(FIRE_PATH, "r") as f:
    fires = json.load(f)

# Combine all LA neighborhood polygons into one study-area shape
neighborhood_geometries = [
    make_valid(shape(feature["geometry"]))
    for feature in neighborhoods["features"]
    if feature.get("geometry")
]

study_area = unary_union(neighborhood_geometries)

clipped_features = []

for feature in fires["features"]:
    if not feature.get("geometry"):
        continue

    fire_geom = make_valid(shape(feature["geometry"]))

    if not fire_geom.intersects(study_area):
        continue

    clipped_geom = fire_geom.intersection(study_area)

    if clipped_geom.is_empty:
        continue

    props = feature.get("properties", {})

    clipped_features.append({
        "type": "Feature",
        "properties": {
            "name": props.get("FIRE_NAME"),
            "year": props.get("YEAR_")
        },
        "geometry": mapping(clipped_geom)
    })

output = {
    "type": "FeatureCollection",
    "features": clipped_features
}

with open(OUTPUT_PATH, "w") as f:
    json.dump(output, f)

print(f"Saved {len(clipped_features)} clipped fire features to {OUTPUT_PATH}")