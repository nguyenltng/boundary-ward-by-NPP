import json
import pickle

print("Loading topojson...")

with open(
    "VietnamWardBoundary2025.topojson",
    encoding="utf-8"
) as f:
    topo = json.load(f)

obj = topo["objects"]["VietnamWardBoundary2025"]

ward_index = {}

for geo in obj["geometries"]:
    props = geo["properties"]

    code = str(props["ma"])

    ward_index[code] = {
        "properties": props,
        "topology": {
            "type": "Topology",
            "transform": topo["transform"],
            "arcs": topo["arcs"],
            "objects": {
                "ward": {
                    "type": "GeometryCollection",
                    "geometries": [geo]
                }
            }
        }
    }

print("Saving...")

with open(
    "ward_index.pkl",
    "wb"
) as f:
    pickle.dump(
        ward_index,
        f,
        protocol=pickle.HIGHEST_PROTOCOL
    )

print(
    f"Done. Total: {len(ward_index)}"
)