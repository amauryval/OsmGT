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
            assert topology_gdf.shape[0] == 0
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


def test_if_orthogonal_isochrones_can_be_computed(location_point, isochrone_values):
    data = OsmGt.isochrone_from_source_node(
        location_point, isochrone_values, 3, mode="pedestrian"
    )
    isochrones_polygon_from_location, isochrones_lines_from_location = data

    assert isochrones_polygon_from_location.shape[0] == 3
    assert set(isochrones_polygon_from_location["iso_name"].to_list()) == {
        "2 minutes",
        "5 minutes",
        "10 minutes",
    }
    assert set(isochrones_polygon_from_location.columns.to_list()) == {
        "geometry",
        "iso_name",
        "iso_distance",
    }
    assert "__dissolve__" not in isochrones_polygon_from_location.columns.to_list()

    assert isochrones_lines_from_location.shape[0] > 0
    assert set(isochrones_lines_from_location["iso_name"].to_list()) == {
        "2 minutes",
        "5 minutes",
        "10 minutes",
    }
    assert set(isochrones_lines_from_location.columns.to_list()).intersection(
        {"geometry", "iso_name", "iso_distance"}
    )
    assert "__dissolve__" not in isochrones_lines_from_location.columns.to_list()


def test_if_orthogonal_isochrone_from_distance(location_point, isochrone_values):
    (
        isochrones_polygons_from_location,
        isochrones_lines_from_location,
    ) = OsmGt.isochrone_distance_from_source_node(
        location_point, [1000], 3, mode="pedestrian"
    )

    assert isochrones_polygons_from_location.shape[0] == 1
    assert isochrones_lines_from_location.shape[0] > 0

    assert set(isochrones_polygons_from_location.columns.to_list()) == {
        "geometry",
        "iso_name",
        "iso_distance",
    }
    assert "__dissolve__" not in isochrones_polygons_from_location.columns.to_list()
    assert set(isochrones_polygons_from_location["iso_name"].to_list()) == {
        "20.0 minutes"
    }

    assert set(isochrones_lines_from_location.columns.to_list()).intersection(
        {"geometry", "iso_name", "iso_distance"}
    )
    assert "__dissolve__" not in isochrones_lines_from_location.columns.to_list()
    assert set(isochrones_lines_from_location["iso_name"].to_list()) == {"20.0 minutes"}

    # check if output geom are correctly built
    geometries = isochrones_polygons_from_location["geometry"].to_list()
    for geom in geometries:

        for geom_to_test in geometries:

            if not geom.equals(geom_to_test):
                assert not geom.intersects(geom_to_test)
            else:
                assert geom.intersects(geom_to_test)

    assert isochrones_lines_from_location["geometry"].unary_union.within(
        isochrones_polygons_from_location["geometry"].unary_union
    )


def test_if_web_isochrone_from_distance(location_point, isochrone_values):
    (
        isochrones_polygons_from_location,
        isochrones_lines_from_location,
    ) = OsmGt.isochrone_distance_from_source_node(
        location_point, [1000], 3, mode="pedestrian", display_mode="web"
    )

    assert isochrones_polygons_from_location.shape[0] == 1
    assert isochrones_lines_from_location.shape[0] > 0

    assert set(isochrones_polygons_from_location.columns.to_list()) == {
        "geometry",
        "iso_name",
        "iso_distance",
    }
    assert "__dissolve__" not in isochrones_polygons_from_location.columns.to_list()
    assert set(isochrones_polygons_from_location["iso_name"].to_list()) == {
        "20.0 minutes"
    }

    assert set(isochrones_lines_from_location.columns.to_list()).intersection(
        {"geometry", "iso_name", "iso_distance"}
    )
    assert "__dissolve__" not in isochrones_lines_from_location.columns.to_list()
    assert set(isochrones_lines_from_location["iso_name"].to_list()) == {"20.0 minutes"}

    # check if output geom are correctly built
    geometries = isochrones_polygons_from_location["geometry"].to_list()
    for geom in geometries:

        for geom_to_test in geometries:

            if not geom.equals(geom_to_test):
                assert not geom.intersects(geom_to_test)
            else:
                assert geom.intersects(geom_to_test)

    assert isochrones_lines_from_location["geometry"].unary_union.within(
        isochrones_polygons_from_location["geometry"].unary_union
    )


def test_if_shortest_path_from_location_with_duplicated_nodes_pairs(
    start_and_end_nodes, shortest_path_default_columns_from_output
):
    shortest_paths = OsmGt.shortest_path_from_location(
        "Roanne", [start_and_end_nodes, start_and_end_nodes,], mode="pedestrian",
    )
    assert shortest_paths.columns.to_list() == shortest_path_default_columns_from_output
    assert len(shortest_paths["osm_ids"]) > 0
    assert shortest_paths.shape[0] == 1


def test_if_shortest_path_from_bbox_with_duplicated_nodes_pairs(
    bbox_values_3, start_and_end_nodes, shortest_path_default_columns_from_output
):
    shortest_paths = OsmGt.shortest_path_from_bbox(
        bbox_values_3, [start_and_end_nodes, start_and_end_nodes,], mode="pedestrian",
    )
    assert shortest_paths.columns.to_list() == shortest_path_default_columns_from_output
    assert len(shortest_paths["osm_ids"]) > 0
    assert len(shortest_paths["osm_urls"]) > 0
    assert shortest_paths.shape[0] == 1


def test_if_shortest_path_from_location_with_an_outside_nodes_pairs(
    start_and_end_nodes, start_and_end_nodes_2
):
    with pytest.raises(AdditionalNodesOutsideWorkingArea) as excinfo:
        _ = OsmGt.shortest_path_from_location(
            "roanne", [start_and_end_nodes, start_and_end_nodes_2,], mode="pedestrian",
        )
        assert (
            "These following points are outside the working area: POINT (-74.00411 40.722584), POINT (-74.00020499999999 40.721494)"
            == str(excinfo.value)
        )


def test_if_shortest_path_from_bbox_with_an_outside_nodes_pairs(
    bbox_values_3, start_and_end_nodes, start_and_end_nodes_2
):
    with pytest.raises(AdditionalNodesOutsideWorkingArea) as excinfo:
        _ = OsmGt.shortest_path_from_bbox(
            bbox_values_3,
            [start_and_end_nodes, start_and_end_nodes_2,],
            mode="pedestrian",
        )
        assert (
            "These following points are outside the working area: POINT (-74.00411 40.722584), POINT (-74.00020499999999 40.721494)"
            == str(excinfo.value)
        )


def test_if_shortest_path_from_location_with_an_outside_node_on_pairs(
    start_and_end_nodes, start_and_end_nodes_3
):
    with pytest.raises(AdditionalNodesOutsideWorkingArea) as excinfo:
        _ = OsmGt.shortest_path_from_location(
            "roanne", [start_and_end_nodes, start_and_end_nodes_3,], mode="pedestrian",
        )
        assert (
            "These following points are outside the working area: POINT (-74.00411 40.722584)"
            == str(excinfo.value)
        )


def test_if_shortest_path_from_bbox_with_an_outside_node_on_pairs(
    bbox_values_3, start_and_end_nodes, start_and_end_nodes_3
):
    with pytest.raises(AdditionalNodesOutsideWorkingArea) as excinfo:
        _ = OsmGt.shortest_path_from_bbox(
            bbox_values_3,
            [start_and_end_nodes, start_and_end_nodes_3,],
            mode="pedestrian",
        )
        assert (
            "These following points are outside the working area: POINT (-74.00411 40.722584)"
            == str(excinfo.value)
        )
