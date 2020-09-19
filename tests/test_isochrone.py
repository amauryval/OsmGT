import pytest

from osmgt import OsmGt


def test_isochrones_from_times(
    location_point,
    isochrone_values,
    isochrones_polygons_output_default_columns,
    isochrones_lines_output_default_columns,
):
    output_data = OsmGt.isochrone_from_source_node(
        location_point, list(isochrone_values), 3, mode="pedestrian"
    )
    isochrones_polygons, isochrones_lines = output_data

    # polygons
    assert isochrones_polygons.shape[0] == 4
    assert set(isochrones_polygons["iso_name"].to_list()) == isochrone_values
    assert isochrones_polygons_output_default_columns.issubset(
        set(isochrones_polygons.columns.to_list())
    )
    assert "__dissolve__" not in isochrones_polygons.columns.to_list()
    # check if output geom are correctly built
    geometries = isochrones_polygons["geometry"].to_list()
    geometries_area_sorted = sorted(
        list([(geom.area, geom) for geom in geometries]), reverse=True
    )
    print(geometries_area_sorted)
    geometries_area_sorted = [feature[-1] for feature in geometries_area_sorted]
    geometries_parent_and_child = [
        (x[0], x[-1])
        for x in list(zip(geometries_area_sorted, geometries_area_sorted[1:]))
    ]
    for parent, child in geometries_parent_and_child:
        assert not child.within(parent)

    # lines
    assert isochrones_lines.shape[0] > 0
    assert set(isochrones_lines["iso_name"].to_list()) == isochrone_values
    assert isochrones_lines_output_default_columns.issubset(
        set(isochrones_lines.columns.to_list())
    )
    assert "__dissolve__" not in isochrones_lines.columns.to_list()
    assert isochrones_lines["geometry"].unary_union.within(
        isochrones_polygons["geometry"].unary_union
    )

def test_isochrone_from_distance(
    location_point,
    isochrone_values,
    isochrones_polygons_output_default_columns,
    isochrones_lines_output_default_columns,
):
    (
        isochrones_polygons,
        isochrones_lines,
    ) = OsmGt.isochrone_distance_from_source_node(
        location_point, [1000], 3, mode="pedestrian"
    )

    # polygons
    assert isochrones_polygons.shape[0] == 1
    assert set(isochrones_polygons["iso_name"].to_list()) == {20}
    assert isochrones_polygons_output_default_columns.issubset(
        set(isochrones_polygons.columns.to_list())
    )
    assert "__dissolve__" not in isochrones_polygons.columns.to_list()

    # lines
    assert isochrones_lines.shape[0] > 0
    assert set(isochrones_lines["iso_name"].to_list()) == {20}
    assert isochrones_lines_output_default_columns.issubset(
        set(isochrones_lines.columns.to_list())
    )
    assert "__dissolve__" not in isochrones_lines.columns.to_list()
    assert isochrones_lines["geometry"].unary_union.within(
        isochrones_polygons["geometry"].unary_union
    )
