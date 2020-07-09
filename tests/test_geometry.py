from osmgt.geometry.nodes_topology import NodesTopology

from osmgt.compoments.core import OsmGtCore


def test_connect_lines(some_line_features, some_point_features):
    raw_data_topology_rebuild = NodesTopology(
        OsmGtCore().logger, some_line_features, some_point_features
    ).run()
    all_uuid = [f["properties"]["uuid"] for f in raw_data_topology_rebuild]

    assert len(raw_data_topology_rebuild) == 17
    # check duplicated
    assert len(set(all_uuid)) == len(all_uuid)
    assert set(all_uuid) == set([
        "10_0",
        "10_1",
        "10_2",
        "10_3",
        "10_4",
        "10_5",
        "10_6",
        "10_7",
        "11_0",
        "11_1",
        "3_0",
        "1_0",
        "2_0",
        "8_0",
        "9_0",
        "7_0",
        "6_0"
    ])
