import pytest

from osmgt import OsmGt


def test_run_from_location_name_func(pois_default_columns_from_output, roads_default_columns_from_output):
    location_name = "roanne"
    poi_from_web_found_gdf = OsmGt.poi_from_location(location_name).get_gdf()

    network_from_web_found = OsmGt.roads_from_location(
        location_name, poi_from_web_found_gdf
    )
    _ = network_from_web_found.get_graph()

    network_from_web_found_gdf = network_from_web_found.get_gdf()

    # check POI
    assert poi_from_web_found_gdf.shape[0] > 0
    assert poi_from_web_found_gdf.shape[-1] > 0
    all_values = list(poi_from_web_found_gdf["uuid"].values)
    assert len(set(all_values)) == len(all_values)
    columns_computed = poi_from_web_found_gdf.columns
    for colunm_expected in pois_default_columns_from_output:
        assert colunm_expected in columns_computed

    # check network
    assert network_from_web_found_gdf.shape[0] > 0
    assert network_from_web_found_gdf.shape[-1] > 0
    all_values = list(network_from_web_found_gdf["uuid"].values)
    assert len(set(all_values)) == len(all_values)
    columns_computed = network_from_web_found_gdf.columns
    for colunm_expected in roads_default_columns_from_output:
        assert colunm_expected in columns_computed


def test_run_from_bbox_func(pois_default_columns_from_output, roads_default_columns_from_output):
    bbox_value = (46.019674567761, 4.0237426757812, 46.072575637028, 4.1220188140869)
    poi_from_web_found_gdf = OsmGt.poi_from_bbox(bbox_value).get_gdf()

    network_from_web_found = OsmGt.roads_from_bbox(bbox_value, poi_from_web_found_gdf)
    _ = network_from_web_found.get_graph()
    network_from_web_found_gdf = network_from_web_found.get_gdf()

    # check POI
    assert poi_from_web_found_gdf.shape[0] > 0
    assert poi_from_web_found_gdf.shape[-1] > 0
    all_values = list(poi_from_web_found_gdf["uuid"].values)
    assert len(set(all_values)) == len(all_values)
    columns_computed = poi_from_web_found_gdf.columns
    for colunm_expected in pois_default_columns_from_output:
        assert colunm_expected in columns_computed

    # check network
    assert network_from_web_found_gdf.shape[0] > 0
    assert network_from_web_found_gdf.shape[-1] > 0
    all_values = list(network_from_web_found_gdf["uuid"].values)
    assert len(set(all_values)) == len(all_values)
    columns_computed = network_from_web_found_gdf.columns
    for colunm_expected in roads_default_columns_from_output:
        assert colunm_expected in columns_computed
