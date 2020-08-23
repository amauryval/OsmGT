import pytest

from osmgt import OsmGt

from graph_tool.topology import shortest_path


def test_run_from_location_name_func(
    pois_default_columns_from_output, roads_default_columns_from_output
):
    location_name = "roanne"
    poi_from_web_found_gdf = OsmGt.poi_from_location(location_name).get_gdf()

    network_from_web_found = OsmGt.roads_from_location(
        location_name, "pedestrian", poi_from_web_found_gdf
    )
    graph_computed = network_from_web_found.get_graph()

    network_from_web_found_gdf = network_from_web_found.get_gdf()

    # check POI
    assert poi_from_web_found_gdf.shape[0] > 0
    assert poi_from_web_found_gdf.shape[-1] > 0
    all_values = list(poi_from_web_found_gdf["topo_uuid"].values)
    assert len(set(all_values)) == len(all_values)
    columns_computed = poi_from_web_found_gdf.columns
    for colunm_expected in pois_default_columns_from_output:
        assert colunm_expected in columns_computed

    # check network
    assert network_from_web_found_gdf.shape[0] > 0
    print(network_from_web_found_gdf.columns)
    assert network_from_web_found_gdf.shape[-1] > 0
    all_uuid_values = list(network_from_web_found_gdf["topo_uuid"].values)
    assert len(set(all_uuid_values)) == len(all_uuid_values)
    columns_computed = network_from_web_found_gdf.columns
    for colunm_expected in roads_default_columns_from_output:
        assert colunm_expected in columns_computed

    # check graph
    assert len(list(graph_computed.edges())) > 0
    assert len(list(graph_computed.vertices())) > 0
    assert type(graph_computed.vertices_content) == dict
    assert len(graph_computed.vertices_content) > 0


def test_run_from_bbox_func(
    pois_default_columns_from_output, roads_default_columns_from_output
):
    bbox_value = (4.0237426757812, 46.019674567761, 4.1220188140869, 46.072575637028)
    poi_from_web_found_gdf = OsmGt.poi_from_bbox(bbox_value).get_gdf()

    network_from_web_found = OsmGt.roads_from_bbox(
        bbox_value, "vehicle", poi_from_web_found_gdf
    )
    graph_computed = network_from_web_found.get_graph()

    network_from_web_found_gdf = network_from_web_found.get_gdf()

    # check POI
    assert poi_from_web_found_gdf.shape[0] > 0
    assert poi_from_web_found_gdf.shape[-1] > 0
    all_values = list(poi_from_web_found_gdf["topo_uuid"].values)
    assert len(set(all_values)) == len(all_values)
    columns_computed = poi_from_web_found_gdf.columns
    for colunm_expected in pois_default_columns_from_output:
        assert colunm_expected in columns_computed

    # check network
    assert network_from_web_found_gdf.shape[0] > 0
    assert network_from_web_found_gdf.shape[-1] > 0
    all_uuid_values = list(network_from_web_found_gdf["topo_uuid"].values)
    assert len(set(all_uuid_values)) == len(all_uuid_values)

    columns_computed = network_from_web_found_gdf.columns
    for colunm_expected in roads_default_columns_from_output:
        assert colunm_expected in columns_computed

    # check graph
    assert len(list(graph_computed.edges())) > 0
    assert len(list(graph_computed.vertices())) > 0
    assert type(graph_computed.vertices_content) == dict
    assert len(graph_computed.vertices_content) > 0


def test_run_from_bbox_func_usa(
    pois_default_columns_from_output, roads_default_columns_from_output
):
    bbox_value = (-74.018433, 40.718087, -73.982749, 40.733356)
    poi_from_web_found_gdf = OsmGt.poi_from_bbox(bbox_value).get_gdf()

    network_from_web_found = OsmGt.roads_from_bbox(
        bbox_value, additionnal_nodes=poi_from_web_found_gdf
    )
    graph_computed = network_from_web_found.get_graph()

    network_from_web_found_gdf = network_from_web_found.get_gdf()

    # check POI
    assert poi_from_web_found_gdf.shape[0] > 0
    assert poi_from_web_found_gdf.shape[-1] > 0
    all_values = list(poi_from_web_found_gdf["topo_uuid"].values)
    assert len(set(all_values)) == len(all_values)
    columns_computed = poi_from_web_found_gdf.columns
    for colunm_expected in pois_default_columns_from_output:
        assert colunm_expected in columns_computed

    # check network
    assert network_from_web_found_gdf.shape[0] > 0
    assert network_from_web_found_gdf.shape[-1] > 0
    all_uuid_values = list(network_from_web_found_gdf["topo_uuid"].values)
    assert len(set(all_uuid_values)) == len(all_uuid_values)

    columns_computed = network_from_web_found_gdf.columns
    for colunm_expected in roads_default_columns_from_output:
        assert colunm_expected in columns_computed

    # check graph
    assert len(list(graph_computed.edges())) > 0
    assert len(list(graph_computed.vertices())) > 0
    assert type(graph_computed.vertices_content) == dict
    assert len(graph_computed.vertices_content) > 0


def test_if_path_can_be_computed(points_gdf_from_coords):
    # TODO add the same test with bbox...
    location_name = "roanne"
    poi_from_web_found_gdf = OsmGt.poi_from_location(location_name).get_gdf()

    network_from_web_found = OsmGt.roads_from_location(
        location_name, "vehicle", poi_from_web_found_gdf
    )

    graph_computed = network_from_web_found.get_graph()
    network_from_web_found_gdf = network_from_web_found.get_gdf()

    start_node = (
        poi_from_web_found_gdf[poi_from_web_found_gdf["topo_uuid"] == 47]
        .iloc[0]["geometry"]
        .wkt
    )
    end_node = (
        poi_from_web_found_gdf[poi_from_web_found_gdf["topo_uuid"] == 63]
        .iloc[0]["geometry"]
        .wkt
    )

    source_vertex = graph_computed.find_vertex_from_name(start_node)
    target_vertex = graph_computed.find_vertex_from_name(end_node)

    path_vertices, path_edges = shortest_path(
        graph_computed,
        source=source_vertex,
        target=target_vertex,
        weights=graph_computed.edge_weights,
    )

    # get path by using edge names
    path_ids = [graph_computed.edge_names[edge] for edge in path_edges]
    print(path_ids)
    assert "added_47" in path_ids[0]
    assert "added_63" in path_ids[-1]

    network_data = network_from_web_found_gdf.copy(deep=True)
    network_data = network_data[network_data["topo_uuid"].isin(path_ids)]

    assert "added_47_forward" in path_ids
    # assert "469_backward" in path_ids
    assert network_data.shape[0] == 27


def test_if_isochrones_can_be_computed(location_point, isochrone_values):
    (
        isochrones_polygon_from_location,
        isochrones_lines_from_location,
    ) = OsmGt.isochrone_from_coordinates(
        location_point, isochrone_values, 3, mode="pedestrian"
    )
    assert isochrones_polygon_from_location.shape[0] == 3
    assert set(isochrones_polygon_from_location["iso_name"].to_list()) == set(
        isochrone_values
    )

    assert isochrones_lines_from_location.shape[0] > 0
    assert set(isochrones_lines_from_location["iso_name"].to_list()) == set(
        isochrone_values
    )
