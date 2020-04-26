import pytest

from osmgt.apis.overpass import OverpassApi
from osmgt.apis.overpass import ErrorOverpassApi

from shapely.geometry import Point
from shapely.geometry import LineString
from shapely.geometry import Polygon


def test_api_overpass_building_polygons():
    bbox_value = "(45.7623544241241049, 4.8276513500527214, 45.7632135219428235, 4.8288282825955848)"
    query = f'(way{bbox_value}["building"];relation{bbox_value}["building"];);out geom;(._;>;);out skel qt;'

    osm_data = OverpassApi(query)

    data_points = osm_data.to_points()
    assert data_points.shape[0] == 474
    assert data_points.shape[-1] == 1
    assert all(map(lambda x: isinstance(x, Point), data_points["geometry"]))

    data_lines = osm_data.to_linestrings()
    assert data_lines.shape[0] == 34
    assert data_lines.shape[-1] == 11
    assert all(map(lambda x: isinstance(x, LineString), data_lines["geometry"]))


def test_api_overpass_railway_lines():
    bbox_value = "(45.707486, 4.771849, 45.808425, 4.898393)"
    query = f'way{bbox_value}["railway"="rail"];out geom;(._;>;);'

    osm_data = OverpassApi(query)

    data_lines = osm_data.to_linestrings()
    assert data_lines.shape[0] == 1604
    assert data_lines.shape[-1] == 40
    assert all(map(lambda x: isinstance(x, LineString), data_lines["geometry"]))

    with pytest.raises(ErrorOverpassApi) as exception_info:
        _ = osm_data.to_points()


def test_api_overpass_stops_points():
    bbox_value = "(45.707486, 4.771849, 45.808425, 4.898393)"
    query = f'node{bbox_value}["highway"="stop"];out geom;(._;>;);'

    osm_data = OverpassApi(query)

    data_points = osm_data.to_points()
    assert data_points.shape[0] == 313
    assert data_points.shape[-1] == 8
    assert all(map(lambda x: isinstance(x, Point), data_points["geometry"]))

    with pytest.raises(ErrorOverpassApi) as exception_info:
        _ = osm_data.to_linestrings()
