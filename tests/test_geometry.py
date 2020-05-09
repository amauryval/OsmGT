from osmgt.geometry.reprojection import ogr_reproject

from osmgt.geometry.nodes_topology import NodesTopology

from osmgt.compoments.core import OsmGtCore


def test_reprojection_same_epsg(point_a, epsg_4326):
    reprojected = ogr_reproject(point_a, epsg_4326, epsg_4326)
    assert reprojected.equals(point_a)


def test_reprojection_to_an_other_epsg(point_a, epsg_4326, epsg_2154):
    reprojected = ogr_reproject(point_a, epsg_4326, epsg_2154)
    reprojected_reverted = ogr_reproject(point_a, epsg_4326, epsg_2154)

    assert not reprojected.equals(point_a)
    assert not point_a.equals(reprojected_reverted)


def test_connect_lines(some_line_features, some_point_features):
    raw_data_topology_rebuild = NodesTopology(
        OsmGtCore().logger, some_line_features, some_point_features
    ).run()
    all_uuid = [f["properties"]["uuid"] for f in raw_data_topology_rebuild]

    assert len(raw_data_topology_rebuild) == 9
    # check duplicated
    assert len(set(all_uuid)) == len(all_uuid)
    assert set(all_uuid) == set(
        ["10_0", "10_1", "10_2", "10_3", "11_0", "11_1", "1_0", "2_0", "3_0"]
    )
