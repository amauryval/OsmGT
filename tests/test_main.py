import pytest

from osmgt import OsmGt

import graph_tool.all as gt


def test_run_from_location_name_func(pois_default_columns_from_output, roads_default_columns_from_output):
    location_name = "roanne"
    poi_from_web_found_gdf = OsmGt.poi_from_location(location_name).get_gdf()

    network_from_web_found = OsmGt.roads_from_location(
        location_name, poi_from_web_found_gdf
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

    #check graph
    assert len(list(graph_computed.edges())) > 0
    assert len(list(graph_computed.vertices())) > 0
    assert type(graph_computed.vertices_content) == dict
    assert len(graph_computed.vertices_content) > 0


def test_run_from_bbox_func(pois_default_columns_from_output, roads_default_columns_from_output):
    bbox_value = (46.019674567761, 4.0237426757812, 46.072575637028, 4.1220188140869)
    poi_from_web_found_gdf = OsmGt.poi_from_bbox(bbox_value).get_gdf()

    network_from_web_found = OsmGt.roads_from_bbox(bbox_value, poi_from_web_found_gdf)
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
    assert "183705011_forward" in all_id_values
    assert "183705011_backward" in all_id_values

    columns_computed = network_from_web_found_gdf.columns
    for colunm_expected in roads_default_columns_from_output:
        assert colunm_expected in columns_computed

    #check graph
    assert len(list(graph_computed.edges())) > 0
    assert len(list(graph_computed.vertices())) > 0
    assert type(graph_computed.vertices_content) == dict
    assert len(graph_computed.vertices_content) > 0


def test_run_from_bbox_func_usa(pois_default_columns_from_output, roads_default_columns_from_output):
    bbox_value = (40.718087, -74.018433, 40.733356, -73.982749)
    poi_from_web_found_gdf = OsmGt.poi_from_bbox(bbox_value).get_gdf()

    network_from_web_found = OsmGt.roads_from_bbox(bbox_value, poi_from_web_found_gdf)
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

    all_id_values = list(network_from_web_found_gdf["id"].values)
    assert len(set(all_id_values)) == len(all_id_values)
    assert "5669279_forward" in all_id_values
    assert "5669279_backward" in all_id_values

    columns_computed = network_from_web_found_gdf.columns
    for colunm_expected in roads_default_columns_from_output:
        assert colunm_expected in columns_computed

    #check graph
    assert len(list(graph_computed.edges())) > 0
    assert len(list(graph_computed.vertices())) > 0
    assert type(graph_computed.vertices_content) == dict
    assert len(graph_computed.vertices_content) > 0


def test_if_graph_works(points_gdf_from_coords):

    location_name = "roanne"
    poi_from_web_found_gdf = OsmGt.poi_from_location(location_name).get_gdf()

    network_from_web_found = OsmGt.roads_from_location(
        location_name, poi_from_web_found_gdf
    )

    graph_computed = network_from_web_found.get_graph()
    network_from_web_found_gdf = network_from_web_found.get_gdf()

    start_node = poi_from_web_found_gdf[poi_from_web_found_gdf['topo_uuid'] == 47].iloc[0]["geometry"].wkt
    end_node = poi_from_web_found_gdf[poi_from_web_found_gdf['topo_uuid'] == 63].iloc[0]["geometry"].wkt

    source_vertex = graph_computed.find_vertex_from_name(start_node)
    target_vertex = graph_computed.find_vertex_from_name(end_node)
    print(start_node, end_node)
    from graph_tool.topology import shortest_path
    path_vertices, path_edges = shortest_path(
        graph_computed,
        source=source_vertex,
        target=target_vertex,
        weights=graph_computed.edge_weights
    )

    # get path by using edge names
    path_ids = [
        graph_computed.edge_names[edge]
        for edge in path_edges
    ]
    print(path_ids)
    assert "added_47" in path_ids[0]
    assert "added_63" in path_ids[-1]

    shortest_path = network_from_web_found_gdf.copy(deep=True)
    shortest_path = shortest_path[shortest_path['topo_uuid'].isin(path_ids)]

    assert "added_47_forward" in path_ids
    assert "1500_4_backward" in path_ids
    assert len(path_ids) == 87
    assert shortest_path.shape[0] == 87

