import pytest

from osmgt import OsmGt

from osmgt.compoments.roads import AdditionalNodesOutsideWorkingArea


def output_data_common_asserts(
    poi_from_web_found_gdf,
    network_from_web_found_gdf,
    default_columns_from_output,
    graph_computed,
):
    # check POI
    if poi_from_web_found_gdf is not None:
        assert poi_from_web_found_gdf.shape[0] > 0
        assert poi_from_web_found_gdf.shape[-1] > 0
        # check all values are unique
        all_values = list(poi_from_web_found_gdf["topo_uuid"].values)
        assert len(set(all_values)) == len(all_values)
        # check columns output
        columns_computed = poi_from_web_found_gdf.columns
        for colunm_expected in default_columns_from_output:
            assert colunm_expected in columns_computed

    # check network
    assert network_from_web_found_gdf.shape[0] > 0
    assert network_from_web_found_gdf.shape[-1] > 0
    # check all values are unique
    all_uuid_values = list(network_from_web_found_gdf["topo_uuid"].values)
    assert len(set(all_uuid_values)) == len(all_uuid_values)

    # check columns output
    columns_computed = network_from_web_found_gdf.columns
    for colunm_expected in default_columns_from_output:
        assert colunm_expected in columns_computed

    # check graph
    assert len(list(graph_computed.edges())) > 0
    assert len(list(graph_computed.vertices())) > 0
    assert type(graph_computed.vertices_content) == dict
    assert len(graph_computed.vertices_content) > 0


def test_run_from_location_name_with_additional_nodes(default_columns_from_output):
    location_name = "roanne"
    poi_from_web_found_gdf = OsmGt.pois_from_location(location_name).get_gdf()

    network_from_web_found = OsmGt.roads_from_location(
        location_name, "pedestrian", poi_from_web_found_gdf
    )
    graph_computed = network_from_web_found.get_graph()
    network_from_web_found_gdf = network_from_web_found.get_gdf()

    output_data_common_asserts(
        poi_from_web_found_gdf,
        network_from_web_found_gdf,
        default_columns_from_output,
        graph_computed,
    )

    network_from_web_found_topology_gdfs = network_from_web_found.topology_checker()

    assert {
        "lines_unchanged",
        "lines_added",
        "lines_split",
        "nodes_added",
        "intersections_added",
    } == set(network_from_web_found_topology_gdfs.keys())
    for topology_gdf in network_from_web_found_topology_gdfs.values():
        assert topology_gdf.shape[0] > 0
        assert topology_gdf.shape[1] == 5


def test_run_from_location_name_without_additional_nodes(default_columns_from_output):
    location_name = "roanne"

    network_from_web_found = OsmGt.roads_from_location(location_name, "pedestrian")
    graph_computed = network_from_web_found.get_graph()
    network_from_web_found_gdf = network_from_web_found.get_gdf()

    output_data_common_asserts(
        None, network_from_web_found_gdf, default_columns_from_output, graph_computed,
    )

    network_from_web_found_topology_gdfs = network_from_web_found.topology_checker()

    assert {
        "lines_unchanged",
        "lines_added",
        "lines_split",
        "nodes_added",
        "intersections_added",
    } == set(network_from_web_found_topology_gdfs.keys())
    for title, topology_gdf in network_from_web_found_topology_gdfs.items():
        if title in ["nodes_added", "lines_added"]:
            assert topology_gdf.shape[0] == 0
        else:
            assert topology_gdf.shape[0] > 0
        assert topology_gdf.shape[1] == 5


def test_run_from_bbox_func(bbox_values_1, default_columns_from_output):

    poi_from_web_found_gdf = OsmGt.pois_from_bbox(bbox_values_1).get_gdf()

    network_from_web_found = OsmGt.roads_from_bbox(
        bbox_values_1, "vehicle", poi_from_web_found_gdf
    )
    graph_computed = network_from_web_found.get_graph()
    network_from_web_found_gdf = network_from_web_found.get_gdf()

    network_from_web_found_topology_gdfs = network_from_web_found.topology_checker()

    output_data_common_asserts(
        poi_from_web_found_gdf,
        network_from_web_found_gdf,
        default_columns_from_output,
        graph_computed,
    )

    assert {
        "lines_unchanged",
        "lines_added",
        "lines_split",
        "nodes_added",
        "intersections_added",
    } == set(network_from_web_found_topology_gdfs.keys())
    for title, topology_gdf in network_from_web_found_topology_gdfs.items():
        if title in ["nodes_added", "lines_added"]:
            assert topology_gdf.shape[0] > 0
        else:
            assert topology_gdf.shape[0] > 0
        assert topology_gdf.shape[1] == 5


def test_run_from_bbox_func_usa(bbox_values_2, default_columns_from_output):
    poi_from_web_found_gdf = OsmGt.pois_from_bbox(bbox_values_2).get_gdf()

    network_from_web_found = OsmGt.roads_from_bbox(
        bbox_values_2, additional_nodes=poi_from_web_found_gdf
    )
    graph_computed = network_from_web_found.get_graph()
    network_from_web_found_gdf = network_from_web_found.get_gdf()

    output_data_common_asserts(
        poi_from_web_found_gdf,
        network_from_web_found_gdf,
        default_columns_from_output,
        graph_computed,
    )
