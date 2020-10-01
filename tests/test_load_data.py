import pytest

from osmgt import OsmGt

from osmgt.compoments.core import ErrorOsmGtCore


def shared_asserts(
    poi_from_web_found_gdf,
    network_from_web_found_gdf,
    default_pois_columns_from_output,
    default_network_columns_from_output,
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
        columns_output = set(list(poi_from_web_found_gdf.columns))
        default_network_columns_from_output.issubset(columns_output)

    # check network
    assert network_from_web_found_gdf.shape[0] > 0
    assert network_from_web_found_gdf.shape[-1] > 0
    # check all values are unique
    all_uuid_values = list(network_from_web_found_gdf["topo_uuid"].values)
    assert len(set(all_uuid_values)) == len(all_uuid_values)

    # check columns output
    columns_output = set(list(network_from_web_found_gdf.columns))
    default_network_columns_from_output.issubset(columns_output)

    # check graph
    assert len(list(graph_computed.edges())) > 0
    assert len(list(graph_computed.vertices())) > 0
    assert type(graph_computed.vertices_content) == dict
    assert len(graph_computed.vertices_content) > 0


def test_get_pois_from_an_unexisting_location():
    location_name = "dsfsdfsdf"

    with pytest.raises(ErrorOsmGtCore) as excinfo:

        _ = OsmGt.pois_from_location(location_name)
        assert "Location not found!" == str(excinfo.value)


def test_run_from_location_name_with_additional_nodes(
    default_output_pois_columns, default_output_network_columns
):
    location_name = "roanne"
    pois_initialized = OsmGt.pois_from_location(location_name)

    pois_study_area = pois_initialized.study_area
    assert pois_study_area.geom_type == "Polygon"

    pois_gdf = pois_initialized.get_gdf()
    network_initialized = OsmGt.roads_from_location(
        location_name, "pedestrian", pois_gdf
    )
    study_area = network_initialized.study_area
    assert study_area.geom_type == "Polygon"

    graph_computed = network_initialized.get_graph()
    network_gdf = network_initialized.get_gdf()

    shared_asserts(
        pois_gdf,
        network_gdf,
        default_output_pois_columns,
        default_output_network_columns,
        graph_computed,
    )

    network_topology_gdfs = network_initialized.topology_checker()
    assert {
        "lines_unchanged",
        "lines_added",
        "lines_split",
        "nodes_added",
        "intersections_added",
    } == set(network_topology_gdfs.keys())
    for topology_gdf in network_topology_gdfs.values():
        assert topology_gdf.shape[0] > 0
        assert topology_gdf.shape[1] == 5


def test_run_from_location_name_without_additional_nodes(
    default_output_pois_columns, default_output_network_columns
):
    location_name = "roanne"

    network_initialized = OsmGt.roads_from_location(location_name, "pedestrian")
    graph_computed = network_initialized.get_graph()
    network_gdf = network_initialized.get_gdf()

    shared_asserts(
        None,
        network_gdf,
        default_output_pois_columns,
        default_output_network_columns,
        graph_computed,
    )

    network_topology_gdfs = network_initialized.topology_checker()
    assert {
        "lines_unchanged",
        "lines_added",
        "lines_split",
        "nodes_added",
        "intersections_added",
    } == set(network_topology_gdfs.keys())
    for title, topology_gdf in network_topology_gdfs.items():
        if title in ["nodes_added", "lines_added"]:
            assert topology_gdf.shape[0] == 0
        else:
            assert topology_gdf.shape[0] > 0
        assert topology_gdf.shape[-1] == 5


def test_run_from_bbox_func(
    bbox_values_1, default_output_pois_columns, default_output_network_columns
):

    pois_initialized = OsmGt.pois_from_bbox(bbox_values_1)

    pois_study_area = pois_initialized.study_area
    assert pois_study_area.geom_type == "Polygon"

    pois_gdf = pois_initialized.get_gdf()

    network_initialized = OsmGt.roads_from_bbox(bbox_values_1, "vehicle", pois_gdf)
    study_area = network_initialized.study_area
    assert study_area.geom_type == "Polygon"

    graph_computed = network_initialized.get_graph()
    network_gdf = network_initialized.get_gdf()

    shared_asserts(
        None,
        network_gdf,
        default_output_pois_columns,
        default_output_network_columns,
        graph_computed,
    )

    network_topology_gdfs = network_initialized.topology_checker()
    assert {
        "lines_unchanged",
        "lines_added",
        "lines_split",
        "nodes_added",
        "intersections_added",
    } == set(network_topology_gdfs.keys())
    for title, topology_gdf in network_topology_gdfs.items():
        if title in ["nodes_added", "lines_added"]:
            assert topology_gdf.shape[0] > 0
        else:
            assert topology_gdf.shape[0] > 0
        assert topology_gdf.shape[-1] == 5


def test_run_from_bbox_func_usa(
    bbox_values_2, default_output_pois_columns, default_output_network_columns
):
    pois_initialized = OsmGt.pois_from_bbox(bbox_values_2)

    pois_study_area = pois_initialized.study_area
    assert pois_study_area.geom_type == "Polygon"

    pois_gdf = pois_initialized.get_gdf()

    network_initialized = OsmGt.roads_from_bbox(
        bbox_values_2, additional_nodes=pois_gdf
    )

    network_study_area = network_initialized.study_area
    assert network_study_area.geom_type == "Polygon"

    graph_computed = network_initialized.get_graph()
    network_gdf = network_initialized.get_gdf()

    shared_asserts(
        None,
        network_gdf,
        default_output_pois_columns,
        default_output_network_columns,
        graph_computed,
    )

    network_topology_gdfs = network_initialized.topology_checker()
    assert {
        "lines_unchanged",
        "lines_added",
        "lines_split",
        "nodes_added",
        "intersections_added",
    } == set(network_topology_gdfs.keys())
    for title, topology_gdf in network_topology_gdfs.items():
        if title in ["nodes_added", "lines_added"]:
            assert topology_gdf.shape[0] > 0
        else:
            assert topology_gdf.shape[0] > 0
        assert topology_gdf.shape[-1] == 5
