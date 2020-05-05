from osmgt.apis.nominatim import NominatimApi
from osmgt.compoments.core import OsmGtCore


def test_find_a_city_by_name():
    output = NominatimApi(logger=OsmGtCore().logger, q="Lyon", limit=1).data()

    assert len(output) == 1
    assert "Lyon" in output[0]["display_name"]
