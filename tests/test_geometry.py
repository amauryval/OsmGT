from osmgt.geometry.network_topology import NetworkTopology

from osmgt.compoments.core import OsmGtCore


def test_connect_lines(some_line_features, some_point_features):
    raw_data_topology_rebuild = NetworkTopology(
        OsmGtCore().logger,
        some_line_features,
        some_point_features,
        "uuid",
        "id",
        "pedestrian",
    ).run()
    all_uuid = [feature["uuid"] for feature in raw_data_topology_rebuild]

    assert len(raw_data_topology_rebuild) == 18
    # check duplicated
    assert len(all_uuid) == len(all_uuid)
    assert len(all_uuid) == len(set(all_uuid))
    assert sorted(all_uuid) == sorted(
        [
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
            "12",
            "added_1",
            "added_2",
            "added_3",
            "added_6",
            "added_7",
            "added_8",
            "added_9",
        ]
    )

    for feature in raw_data_topology_rebuild:
        if feature["topology"] == "unchanged":
            assert "_" not in feature["uuid"]

        if feature["topology"] == "split":
            assert "_" in feature["uuid"]

        if feature["topology"] == "added":
            assert "added_" in feature["uuid"]
