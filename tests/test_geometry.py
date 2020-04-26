import pytest

from osmgt.geometry.reprojection import ogr_reproject

def test_reprojection_same_epsg(point_a, epsg_4326):
    reprojected = ogr_reproject(point_a, epsg_4326, epsg_4326)
    assert reprojected.equals(point_a)

def test_reprojection_to_an_other_epsg(point_a, epsg_4326, epsg_2154):
    reprojected = ogr_reproject(point_a, epsg_4326, epsg_2154)
    reprojected_reverted = ogr_reproject(point_a, epsg_4326, epsg_2154)

    assert not reprojected.equals(point_a)
    assert not point_a.equals(reprojected_reverted)