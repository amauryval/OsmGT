import pytest

from osmgt.apis.overpass import OverpassApi

from osmgt.compoments.osmgt_core import OsmGtCore


def overpass_query_result():
    return OverpassApi(OsmGtCore().logger, "3600134383")


def test_api_overpass_railway_lines():
    osm_data = overpass_query_result().data()

    assert len(osm_data) == 4
