import json
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from shapely.validation import make_valid

NEIGHBORHOODS_PATH = "app/static/neighborhoods.geojson"
FLOOD_PATH = "app/static/flood_raw.geojson"
OUTPUT_PATH = "app/static/flood_clipped.geojson"

with open(NEIGHBORHOODS_PATH, "r") as f:
    neighborhoods = json.load(f)

with open(FLOOD_PATH, "r") as f:
    floods = json.load(f)

# Combine all neighborhood polygons into the exact study area
neighborhood_geometries = [
    make_valid(shape(feature["geometry"]))
    for feature in neighborhoods["features"]
    if feature.get("geometry")
]

study_area = unary_union(neighborhood_geometries)

clipped_features = []

for feature in floods["features"]:
    if not feature.get("geometry"):
        continue

    flood_geom = make_valid(shape(feature["geometry"]))

    if not flood_geom.intersects(study_area):
        continue

    clipped_geom = flood_geom.intersection(study_area)

    if clipped_geom.is_empty:
        continue

    props = feature.get("properties", {})

    clipped_features.append({
        "type": "Feature",
        "properties": {
            "fld_zone": props.get("FLD_ZONE"),
            "zone_subty": props.get("ZONE_SUBTY"),
            "sfha_tf": props.get("SFHA_TF")
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
    f"Saved {len(clipped_features)} clipped flood features "
    f"to {OUTPUT_PATH}"
)