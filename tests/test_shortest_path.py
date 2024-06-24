import pytest

from osmgt import OsmGt

from osmgt.compoments.roads import AdditionalNodesOutsideWorkingArea


def test_if_shortest_path_from_location_with_duplicated_nodes_pairs(
    start_and_end_nodes, shortest_path_output_default_columns
):
    shortest_paths = OsmGt.shortest_path_from_location(
        "Roanne", [start_and_end_nodes, start_and_end_nodes], mode="pedestrian",
    )
    assert set(shortest_paths.columns.to_list()) == shortest_path_output_default_columns
    assert len(shortest_paths["osm_ids"]) > 0
    assert shortest_paths.shape[0] == 1


def test_if_shortest_path_from_bbox_with_duplicated_nodes_pairs(
    bbox_values_3, start_and_end_nodes, shortest_path_output_default_columns
):
    shortest_paths = OsmGt.shortest_path_from_bbox(
        bbox_values_3, [start_and_end_nodes, start_and_end_nodes], mode="pedestrian",
    )
    assert set(shortest_paths.columns.to_list()) == shortest_path_output_default_columns
    assert len(shortest_paths["osm_ids"]) > 0
    assert shortest_paths.shape[0] == 1


def test_if_shortest_path_from_location_with_an_outside_nodes_pairs(
    start_and_end_nodes, start_and_end_nodes_2
):
    with pytest.raises(AdditionalNodesOutsideWorkingArea) as excinfo:
        _ = OsmGt.shortest_path_from_location(
            "roanne", [start_and_end_nodes, start_and_end_nodes_2], mode="pedestrian",
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
            [start_and_end_nodes, start_and_end_nodes_2],
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
            "roanne", [start_and_end_nodes, start_and_end_nodes_3], mode="pedestrian"
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
            [start_and_end_nodes, start_and_end_nodes_3],
            mode="pedestrian",
        )
        assert (
            "These following points are outside the working area: POINT (-74.00411 40.722584)"
            == str(excinfo.value)
        )
