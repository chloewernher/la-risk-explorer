import json
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from shapely.validation import make_valid

NEIGHBORHOODS_PATH = "app/static/neighborhoods.geojson"
AIR_PATH = "app/static/air_raw.geojson"
OUTPUT_PATH = "app/static/air_clipped.geojson"

with open(NEIGHBORHOODS_PATH, "r") as f:
    neighborhoods = json.load(f)

with open(AIR_PATH, "r") as f:
    air = json.load(f)

neighborhood_geometries = [
    make_valid(shape(feature["geometry"]))
    for feature in neighborhoods["features"]
    if feature.get("geometry")
]

study_area = unary_union(neighborhood_geometries)

clipped_features = []

for feature in air["features"]:
    if not feature.get("geometry"):
        continue

    air_geom = make_valid(shape(feature["geometry"]))

    if not air_geom.intersects(study_area):
        continue

    clipped_geom = air_geom.intersection(study_area)

    if clipped_geom.is_empty:
        continue

    props = feature.get("properties", {})

    clipped_features.append({
        "type": "Feature",
        "properties": {
            "pm25": props.get("pm"),
            "ozone": props.get("ozone"),
            "diesel_pm": props.get("diesel"),
            "traffic": props.get("traffic"),
            "toxic_releases": props.get("RSEIhaz"),
            "pesticides": props.get("pest")
        },
        "geometry": mapping(clipped_geom)
    })

output = {
    "type": "FeatureCollection",
    "features": clipped_features
}

with open(OUTPUT_PATH, "w") as f:
    json.dump(output, f)

print(
    f"Saved {len(clipped_features)} clipped air pollution features "
    f"to {OUTPUT_PATH}"
)