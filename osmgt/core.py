from osmgt.apis.nominatim import NominatimApi
from osmgt.apis.overpass import OverpassApi


import geopandas as gpd

from shapely.geometry import Point
from shapely.geometry import LineString

import uuid

import geojson

import numpy as np

from collections import Counter

from more_itertools import split_at

from osmgt.network.graphtools_helper import GraphHelpers
from osmgt.geometry.reprojection import ogr_reproject


class OsmGtCore:

    __NUMBER_OF_NODES_INTERSECTIONS = 2
    __NEXT_INDEX = 1
    __ITEM_LIST_SEPARATOR = "_"
    __GRAPH_FIELDS = {"node_1", "node_2", "geometry", "length"}
    __ID_FIELD = "uuid"

    __INPUT_EPSG = 4326
    __OUTPUT_EPSG = 3857
    __LOCATION_OSM_DEFAULT_ID = 3600000000  # this is it...

    def __init__(self, location_name):
        super().__init__()

        self._location_name = location_name

        self._output = []
        self.__get_data_from_osm()
        self.__cleaning_geometry()

    def __get_data_from_osm(self):
        location_id = NominatimApi(q=self._location_name, limit=1).data()[0]["osm_id"]
        location_id += self.__LOCATION_OSM_DEFAULT_ID
        self._raw_data = OverpassApi(location_osm_id=location_id).data()["elements"]

    def __get_all_ways_found_by_query(self):
        return filter(lambda x: x["type"] == "way", self._raw_data)

    def __cleaning_geometry(self):
        # find all the existing intersection from coordinates
        ways_found = self.__get_all_ways_found_by_query()
        intersections_found = self.find_intersections_from_ways(ways_found)

        ways_found = self.__get_all_ways_found_by_query()
        for feature in ways_found:
            coordinates = list(map(lambda x: frozenset([x["lon"], x["lat"]]), feature["geometry"]))
            points_intersections = set(coordinates).intersection(intersections_found)

            lines_coordinates_rebuild = self._topology_builder(coordinates, points_intersections)

            for line_coordinates in lines_coordinates_rebuild:
                line_coordinates = list(map(tuple, line_coordinates))
                geometry = ogr_reproject(LineString(line_coordinates), self.__INPUT_EPSG, self.__OUTPUT_EPSG)

                data = {
                    "node_1": line_coordinates[0],
                    "node_2": line_coordinates[-1],
                    "geometry": geometry,
                    "length": geometry.length,
                    self.__ID_FIELD: uuid.uuid1()
                }
                data.update(self._get_tags(feature))
                array = np.array(data)

                self._output.append(array)

        self._output = np.stack(self._output)

    def to_numpy_array(self):
        return self._output

    def to_linestrings(self):
        features = []
        for feature in self._output:
            geometry = feature["geometry"]
            properties = {
                key: feature[key] for key in feature.keys()
                if key not in self.__GRAPH_FIELDS
            }
            feature = geojson.Feature(
                geometry=geometry,
                properties=properties
            )
            features.append(feature)

        return self.__to_gdf(features)

    def _topology_builder(self, coordinates, points_intersections):
        is_rebuild = False

        # split coordinates found at intersection to respect the topology
        first_value, *middle_coordinates_values, last_value = coordinates
        for point_intersection in points_intersections:

            if point_intersection in middle_coordinates_values:
                # we get the middle values from coordinates to avoid to catch the first and last value when editing
                middle_coordinates_values.insert(
                    middle_coordinates_values.index(point_intersection),
                    point_intersection
                )
                middle_coordinates_values.insert(
                    middle_coordinates_values.index(point_intersection) + self.__NEXT_INDEX,
                    self.__ITEM_LIST_SEPARATOR
                )
                coordinates = [first_value] + middle_coordinates_values + [last_value]
                is_rebuild = True

        if is_rebuild:
            coordinates = list(split_at(coordinates, lambda x: x == '_'))

        if not is_rebuild:
            coordinates = list([coordinates])

        return coordinates

    def find_intersections_from_ways(self, ways_found):

        all_coord_points = [
            frozenset([coords["lon"], coords["lat"]])
            for feature in ways_found
            for coords in feature["geometry"]
        ]
        intersections_count = Counter(all_coord_points)
        intersections_found = [coord for coord, count in intersections_count.items() if count >= self.__NUMBER_OF_NODES_INTERSECTIONS]
        return set(intersections_found)

    def to_points(self):
        nodes_found = filter(lambda feature: feature["type"] == "node", self._raw_data)

        features = [
            geojson.Feature(
                geometry=Point(feature["lon"], feature["lat"]),
                properties=self._get_tags(feature)
            )
            for feature in nodes_found
        ]
        return self.__to_gdf(features)

    def __to_gdf(self, features):
        output = gpd.GeoDataFrame.from_features(features)
        output.crs = self.__INPUT_EPSG
        # output = output.to_crs(3857)
        return output

    def to_graph(self):
        self.to_numpy_array()
        graph = GraphHelpers(directed=False)

        for feature in self._output:
            graph.add_edge(
                str(feature["node_1"]),
                str(feature["node_2"]),
                feature[self.__ID_FIELD],
                feature["length"],
            )
        return graph

    def _get_tags(self, feature):
        return feature.get("tags", {})
