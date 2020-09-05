import pytest

from osmgt import OsmGt

from osmgt.compoments.roads import AdditionalNodesOutsideWorkingArea


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
