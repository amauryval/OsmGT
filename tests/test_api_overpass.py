import pytest

from osmgt.apis.overpass import OverpassApi
from osmgt.apis.overpass import ErrorOverpassApi

from shapely.geometry import Point
from shapely.geometry import LineString
from shapely.geometry import Polygon


def test_api_overpass_building_polygons(schema_name_not_existing):
    bbox_value = "(45.7623544241241049, 4.8276513500527214, 45.7632135219428235, 4.8288282825955848)"
    query = f'(way{bbox_value}["building"];relation{bbox_value}["building"];);out geom;(._;>;);out skel qt;'

    data_polygon = OverpassApi(query).to_polygons()
    assert data_polygon.shape[0] == 50
    assert data_polygon.shape[-1] == 12
    assert all(map(lambda x: isinstance(x, Polygon), data_polygon["geometry"]))

    data_points = OverpassApi(query).to_points()
    assert data_points.shape[0] == 474
    assert data_points.shape[-1] == 1
    assert all(map(lambda x: isinstance(x, Point), data_points["geometry"]))

    data_lines = OverpassApi(query).to_linestrings()
    assert data_lines.shape[0] == 34
    assert data_lines.shape[-1] == 11
    assert all(map(lambda x: isinstance(x, LineString), data_lines["geometry"]))


def test_api_overpass_railway_lines():
    bbox_value = "(45.707486, 4.771849, 45.808425, 4.898393)"
    query = f'way{bbox_value}["railway"="rail"];out geom;(._;>;);'

    data_lines = OverpassApi(query).to_linestrings()
    assert data_lines.shape[0] == 1604
    assert data_lines.shape[-1] == 40
    assert all(map(lambda x: isinstance(x, LineString), data_lines["geometry"]))

    with pytest.raises(ErrorOverpassApi) as exception_info:
        _ = OverpassApi(query).to_points()

    data_polygons = OverpassApi(query).to_polygons()
    assert data_polygons.shape[0] == 1029
    assert data_polygons.shape[-1] == 37
    assert all(map(lambda x: isinstance(x, Polygon), data_polygons["geometry"]))


def test_api_overpass_stops_points():
    bbox_value = "(45.707486, 4.771849, 45.808425, 4.898393)"
    query = f'node{bbox_value}["highway"="stop"];out geom;(._;>;);'

    data_points = OverpassApi(query).to_points()
    assert data_points.shape[0] == 313
    assert data_points.shape[-1] == 8
    assert all(map(lambda x: isinstance(x, Point), data_points["geometry"]))

    with pytest.raises(ErrorOverpassApi) as exception_info:
        _ = OverpassApi(query).to_linestrings()

    with pytest.raises(ErrorOverpassApi) as exception_info:
        _ = OverpassApi(query).to_polygons()
