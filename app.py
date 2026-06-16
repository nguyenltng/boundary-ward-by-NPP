import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from io import BytesIO
import zipfile

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(
    page_title="NPP Territory",
    layout="wide",
)


# ==================================================
# UTILS
# ==================================================
def normalize_text(value):
    if value is None or pd.isna(value):
        return ""

    text = unicodedata.normalize(
        "NFKC",
        str(value)
    ).strip().lower()

    text = unicodedata.normalize(
        "NFD",
        text
    )

    text = "".join(
        ch
        for ch in text
        if unicodedata.category(ch) != "Mn"
    )

    text = re.sub(
        r"[^0-9a-z\s/-]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def first_existing_column(columns, candidates):
    normalized = {
        normalize_text(col): col
        for col in columns
    }

    for candidate in candidates:
        matched = normalized.get(
            normalize_text(candidate)
        )

        if matched:
            return matched

    return None


# ==================================================
# LOAD GEOJSON
# ==================================================


@st.cache_data
def load_geojson():
    zip_path = "VietnamWardBoundary2025.geojson.zip"

    with zipfile.ZipFile(zip_path, "r") as z:
        geojson_file = next(
            name for name in z.namelist()
            if name.endswith(".geojson")
        )

        with z.open(geojson_file) as f:
            return json.load(f)
        
@st.cache_data
def build_indexes():
    geo = load_geojson()

    geo_index = {}
    admin_index = {}
    ward_only_index = defaultdict(set)

    for feature in geo["features"]:
        p = feature["properties"]

        ward_code = str(
            p["ma"]
        )

        ward_name = normalize_text(
            p["tenhc"]
        )

        province_name = normalize_text(
            p["tentinh"]
        )

        geo_index[
            ward_code
        ] = feature

        admin_index[
            (
                ward_name,
                province_name
            )
        ] = ward_code

        ward_only_index[
            ward_name
        ].add(ward_code)

    return (
        geo_index,
        admin_index,
        ward_only_index
    )


geo_index, admin_index, ward_only_index = (
    build_indexes()
)

# ==================================================
# SESSION
# ==================================================
if "import_result" not in st.session_state:
    st.session_state.import_result = None

if "selected_npp_name" not in st.session_state:
    st.session_state.selected_npp_name = None


# ==================================================
# IMPORT EXCEL
# ==================================================
def parse_import_file(file_bytes):
    df = pd.read_excel(BytesIO(file_bytes))
    df = df.ffill()

    npp_column = first_existing_column(df.columns, ["NPP", "Nhà Phân Phối", "Distributor"])
    ward_column = first_existing_column(df.columns, ["Phường/Xã", "Phường Xã", "Ward"])
    city_column = first_existing_column(df.columns, ["Thành phố", "Tỉnh", "Thành phố/Tỉnh", "Province", "City"])

    missing = []
    if not npp_column:
        missing.append("NPP")
    if not ward_column:
        missing.append("Phường/Xã")
    if not city_column:
        missing.append("Tỉnh/Thành phố")

    if missing:
        return {"distributors": [], "errors": ["Thiếu cột: " + ", ".join(missing)]}

    distributors = defaultdict(lambda: {"name": "", "wards": set()})
    errors = []

    for idx, row in df.iterrows():
        npp = str(row[npp_column]).strip()
        ward = normalize_text(row[ward_column])
        city = normalize_text(row[city_column])

        if not npp or not ward or not city:
            continue

        candidates = ward_only_index.get(ward, set())

        ward_code = None

        # ==================================================
        # LIKE MATCH LOGIC
        # ==================================================
        for code in candidates:
            feature = geo_index.get(code)
            if not feature:
                continue

            props = feature["properties"]

            geo_ward = normalize_text(props.get("tenhc"))
            geo_city = normalize_text(props.get("tentinh"))

            # LIKE both directions
            ward_match = ward in geo_ward or geo_ward in ward
            city_match = city in geo_city or geo_city in city

            if ward_match and city_match:
                ward_code = code
                break

        if not ward_code:
            errors.append(f"Dòng {idx+2}: {row[ward_column]} - {row[city_column]}")
            continue

        distributors[npp]["name"] = npp
        distributors[npp]["wards"].add(ward_code)

    result = []
    for item in distributors.values():
        item["wards"] = list(item["wards"])
        result.append(item)

    return {"distributors": result, "errors": errors}



# ==================================================
# IMPORT UI
# ==================================================
st.sidebar.header(
    "Import Excel"
)

uploaded_file = (
    st.sidebar.file_uploader(
        "Chọn file Excel",
        type=["xlsx"]
    )
)

if uploaded_file is not None:
    file_bytes = (
        uploaded_file.getvalue()
    )

    file_signature = hashlib.sha1(
        file_bytes
    ).hexdigest()

    if (
        st.session_state.get(
            "import_signature"
        )
        != file_signature
    ):
        st.session_state.import_result = (
            parse_import_file(
                file_bytes
            )
        )

        st.session_state.import_signature = (
            file_signature
        )

        st.session_state.selected_npp_name = (
            None
        )

if st.sidebar.button(
    "Xóa dữ liệu"
):
    st.session_state.import_result = None
    st.session_state.import_signature = None
    st.session_state.selected_npp_name = None
    st.rerun()

import_result = (
    st.session_state.import_result
)

if import_result:
    if import_result["errors"]:
        st.warning(
            "\n".join(
                import_result["errors"]
            )
        )

# ==================================================
# NO DATA
# ==================================================
if (
    not import_result
    or not import_result[
        "distributors"
    ]
):
    st.info(
        "Import file Excel để bắt đầu."
    )
    st.stop()

# ==================================================
# SELECT NPP
# ==================================================
npp_names = [
    x["name"]
    for x in import_result[
        "distributors"
    ]
]

if (
    st.session_state
    .selected_npp_name
    not in npp_names
):
    st.session_state.selected_npp_name = (
        npp_names[0]
    )
if "view_npp_name" not in st.session_state:
    st.session_state.view_npp_name = None

# selected_name = st.selectbox(
#     "Chọn Nhà Phân Phối",
#     npp_names,
#     index=npp_names.index(
#         st.session_state
#         .selected_npp_name
#     ),
#     key="selected_npp_name",
# )

col1, col2, col3 = st.columns([3, 1, 6])

with col1:
    selected_name = st.selectbox(
        "Nhà Phân Phối",
        npp_names,
        index=npp_names.index(
            st.session_state.selected_npp_name
        ),
        key="selected_npp_name",
    )

with col2:
    st.write("")
    st.write("")

    if st.button(
        "Xem",
        use_container_width=True
    ):
        st.session_state.view_npp_name = (
            selected_name
        )
if not st.session_state.view_npp_name:
    st.info(
        "Chọn Nhà Phân Phối và nhấn 'Xem'."
    )
    st.stop()

selected_npp = next(
    x
    for x in import_result["distributors"]
    if x["name"]
    == st.session_state.view_npp_name
)


# ==================================================
# FEATURES
# ==================================================
selected_features = []
ward_names = []

for code in selected_npp["wards"]:
    feature = geo_index.get(
        str(code)
    )

    if feature:
        selected_features.append(
            feature
        )
        ward_names.append(
            feature["properties"].get(
                "tenhc",
                ""
            )
        )

if not selected_features:
    st.warning(
        "Không có dữ liệu bản đồ."
    )
    st.stop()

# ==================================================
# MAP
# ==================================================
geo = {
    "type": "FeatureCollection",
    "features": selected_features
}

m = folium.Map(
    location=[16.5, 107.5],
    zoom_start=6,
    tiles="CartoDB positron",
)

folium.GeoJson(
    geo,
    style_function=lambda x: {
        "fillColor": "#ff0000",
        "color": "#ff0000",
        "weight": 2,
        "fillOpacity": 0.7,
    },
    # tooltip=folium.GeoJsonTooltip(
    #     fields=[
    #         "tenhc",
    #         "tentinh"
    #     ],
    #     aliases=[
    #         "Phường/Xã",
    #         "Tỉnh"
    #     ]
    # ),
).add_to(m)

from shapely.geometry import shape

for feature in selected_features:
    geom = shape(feature["geometry"])

    center = geom.centroid

    name = (
        f"{feature['properties']['loai'].title()} "
        f"{feature['properties']['tenhc']}"
    )

    folium.Marker(
        location=[
            center.y,
            center.x,
        ],
        icon=folium.DivIcon(
            html=f"""
            <div style="
                font-size:12px;
                font-weight:bold;
                color:black;
                white-space: nowrap;
                text-shadow:
                    -1px -1px 0 white,
                     1px -1px 0 white,
                    -1px  1px 0 white,
                     1px  1px 0 white;
            ">
                {name}
            </div>
            """
        ),
    ).add_to(m)

bounds = (
    folium.GeoJson(geo)
    .get_bounds()
)

m.fit_bounds(bounds)

# ==================================================
# LAYOUT: DANH SÁCH + BẢN ĐỒ
# ==================================================
col1, col2 = st.columns([2, 10])

with col1:
    st.subheader(
        f"Danh sách phường ({len(ward_names)})"
    )
    
    ward_names_sorted = sorted(
        set(ward_names)
    )
    
    for ward in ward_names_sorted:
        st.caption(f"• {ward}")

with col2:
    st_folium(
        m,
        height=600,
        width=None,
    )