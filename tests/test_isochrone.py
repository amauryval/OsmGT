import pytest

from osmgt import OsmGt


def test_if_orthogonal_isochrones_can_be_computed(location_point, isochrone_values,
                                                  isochrones_polygons_output_default_columns):
    output_data = OsmGt.isochrone_from_source_node(
        location_point, isochrone_values, 3, mode="pedestrian"
    )
    isochrones_polygons, isochrones_lines = output_data

    assert isochrones_polygons.shape[0] == 3
    assert set(isochrones_polygons["iso_name"].to_list()) == {
        "2 minutes",
        "5 minutes",
        "10 minutes",
    }
    assert isochrones_polygons_output_default_columns.issubset(set(isochrones_polygons.columns.to_list()))
    assert "__dissolve__" not in isochrones_polygons.columns.to_list()

    assert isochrones_lines.shape[0] > 0
    assert set(isochrones_lines["iso_name"].to_list()) == {
        "2 minutes",
        "5 minutes",
        "10 minutes",
    }
    assert set(isochrones_lines.columns.to_list()).intersection(
        {"geometry", "iso_name", "iso_distance"}
    )
    assert "__dissolve__" not in isochrones_lines.columns.to_list()


def test_if_orthogonal_isochrone_from_distance(location_point, isochrone_values,
                                               isochrones_polygons_output_default_columns):
    (
        isochrones_polygons,
        isochrones_lines,
    ) = OsmGt.isochrone_distance_from_source_node(
        location_point, [1000], 3, mode="pedestrian"
    )

    assert isochrones_polygons.shape[0] == 1
    assert isochrones_lines.shape[0] > 0

    assert isochrones_polygons_output_default_columns.issubset(set(isochrones_polygons.columns.to_list()))

    assert "__dissolve__" not in isochrones_polygons.columns.to_list()
    assert set(isochrones_polygons["iso_name"].to_list()) == {
        "20.0 minutes"
    }

    assert set(isochrones_lines.columns.to_list()).intersection(
        {"geometry", "iso_name", "iso_distance"}
    )
    assert "__dissolve__" not in isochrones_lines.columns.to_list()
    assert set(isochrones_lines["iso_name"].to_list()) == {"20.0 minutes"}

    # check if output geom are correctly built
    geometries = isochrones_polygons["geometry"].to_list()
    for geom in geometries:

        for geom_to_test in geometries:

            if not geom.equals(geom_to_test):
                assert not geom.intersects(geom_to_test)
            else:
                assert geom.intersects(geom_to_test)

    assert isochrones_lines["geometry"].unary_union.within(
        isochrones_polygons["geometry"].unary_union
    )


def test_if_web_isochrone_from_distance(location_point, isochrone_values):
    (
        isochrones_polygons,
        isochrones_lines,
    ) = OsmGt.isochrone_distance_from_source_node(
        location_point, [1000], 3, mode="pedestrian", display_mode="web"
    )

    assert isochrones_polygons.shape[0] == 1
    assert isochrones_lines.shape[0] > 0

    assert set(isochrones_polygons.columns.to_list()) == {
        "geometry",
        "iso_name",
        "iso_distance",
    }
    assert "__dissolve__" not in isochrones_polygons.columns.to_list()
    assert set(isochrones_polygons["iso_name"].to_list()) == {
        "20.0 minutes"
    }

    assert set(isochrones_lines.columns.to_list()).intersection(
        {"geometry", "iso_name", "iso_distance"}
    )
    assert "__dissolve__" not in isochrones_lines.columns.to_list()
    assert set(isochrones_lines["iso_name"].to_list()) == {"20.0 minutes"}

    # check if output geom are correctly built
    geometries = isochrones_polygons["geometry"].to_list()
    for geom in geometries:

        for geom_to_test in geometries:

            if not geom.equals(geom_to_test):
                assert not geom.intersects(geom_to_test)
            else:
                assert geom.intersects(geom_to_test)

    assert isochrones_lines["geometry"].unary_union.within(
        isochrones_polygons["geometry"].unary_union
    )
