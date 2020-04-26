import geopandas as gpd

from shapely.geometry import Point
from shapely.geometry import LineString

import uuid

import geojson

import numpy as np

from collections import Counter

from more_itertools import split_at

from osmgt.apis.core import ApiCore
from osmgt.network.graphtools_helper import GraphHelpers
from osmgt.geometry.reprojection import ogr_reproject


class ErrorOverpassApi(ValueError):
    pass


class OverpassApi(ApiCore):

    __OVERPASS_URL = "https://www.overpass-api.de/api/interpreter"
    __OVERPASS_QUERY_PREFIX = "[out:json];"
    # __OVERPASS_QUERY_SUFFIX = ";(._;>;);out geom;"
    __OVERPASS_QUERY_SUFFIX = ""


    def __init__(self, location_osm_id):
        super().__init__()

        # TODO : create others filters to get different data
        query = self._get_roads_data(location_osm_id)

        self._query = query
        parameters = self._build_parameters()
        self.__RESULT_QUERY = self.compute_query(self.__OVERPASS_URL, parameters)

    def _build_parameters(self):
        return {"data": f"{self.__OVERPASS_QUERY_PREFIX}{self._query}{self.__OVERPASS_QUERY_SUFFIX}"}

    def _get_roads_data(self, location_osm_id):
        return f'area({location_osm_id})->.searchArea;(way["highway"](area.searchArea););out geom;(._;>;);'

    def data(self):
        return self.__RESULT_QUERY