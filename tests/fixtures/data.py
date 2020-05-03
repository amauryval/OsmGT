import pytest

from shapely.wkt import loads
from shapely.geometry import LineString
from shapely.geometry import Point

import geojson
import geopandas as gpd


wkt_point_a = "Point (30 10 5)"
wkt_point_b = "Point(4 10 3)"
wkt_point_c = "Point (0 0 4)"


def build_geojson_features(input_data):
    all_geojson_features = []
    for feature in input_data:
        feature["properties"]["bounds"] = ", ".join(map(str, feature["geometry"].bounds))

        feature = geojson.Feature(
            geometry=feature["geometry"],
            properties=feature["properties"]
        )
        all_geojson_features.append(feature)
    output_gdf = gpd.GeoDataFrame.from_features(all_geojson_features)

    return output_gdf

@pytest.fixture
def point_a():
    return loads(wkt_point_a)

@pytest.fixture
def point_b():
    return loads(wkt_point_b)

@pytest.fixture
def point_c():
    return loads(wkt_point_c)

@pytest.fixture
def epsg_2154():
    return 2154

@pytest.fixture
def epsg_4326():
    return 4326

@pytest.fixture
def some_line_features():
    all_features = [
        {"geometry": LineString([(4.07114907206290066, 46.03760345278882937), (4.07091681769133018, 46.03699538217645681), (4.07079583285433966, 46.03660928470699787)]), "properties": {"uuid": 10, "field_line": 10}},
    ]
    output_gdf = build_geojson_features(all_features)

    return output_gdf.__geo_interface__["features"]

@pytest.fixture
def some_point_features():
    all_features = [
        {"geometry": Point((4.07083953255024333, 46.03693156996429536)), "properties": {"uuid": 1, "field_point": "1"}},  # on a side
        {"geometry": Point((4.07089961963211167, 46.03664388029959298)), "properties": {"uuid": 2, "field_point": "2"}},  # on a side
        {"geometry": Point((4.07097056291628423, 46.03710105075762726)), "properties": {"uuid": 3, "field_point": "3"}},  # on a side
        {"geometry": Point((4.07114907206290066, 46.03760345278882937)), "properties": {"uuid": 4, "field_point": "4"}},  # at the line start point
        {"geometry": Point((4.07091681769133018, 46.03699538217645681)), "properties": {"uuid": 5, "field_point": "5"}},  # at the middle line point
    ]
    output_gdf = build_geojson_features(all_features)

    return output_gdf