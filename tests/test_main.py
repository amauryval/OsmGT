import pytest

from osmgt import OsmGt


def test_run_main_func():
    location_name = "roanne"
    poi_from_web_found = OsmGt.poi_from_location(location_name).get_gdf()
    network_from_web_found = OsmGt.network_from_location(
        location_name, poi_from_web_found
    ).get_gdf()

    assert network_from_web_found.shape[0] == 3366
    assert network_from_web_found.shape[-1] == 162
    all_values = list(network_from_web_found["uuid"].values)
    assert len(set(all_values)) == len(all_values)
