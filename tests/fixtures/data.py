import pytest

from shapely.wkt import loads

wkt_point_a = "Point (30 10 5)"
wkt_point_b = "Point(4 10 3)"
wkt_point_c = "Point (0 0 4)"



@pytest.fixture
def point_a():
    return loads(wkt_point_a)

@pytest.fixture
def point_b():
    return loads(wkt_point_b)

@pytest.fixture
def point_c():
    return loads(wkt_point_c)

@pytest.fixture
def epsg_2154():
    return 2154

@pytest.fixture
def epsg_4326():
    return 4326