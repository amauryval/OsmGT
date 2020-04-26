import geopandas as gpd

from shapely.geometry import Point
from shapely.geometry import LineString
from shapely.geometry import Polygon

import geojson

import numpy as np

from collections import Counter

from more_itertools import split_at

from osmgt.apis.core import ApiCore
# from osmgt.network.graphtools_helper import GraphHelpers
from osmgt.geometry.reprojection import ogr_reproject


class ErrorOverpassApi(ValueError):
    pass


class OverpassApi(ApiCore):

    __NUMBER_OF_NODES_INTERSECTIONS = 2
    __NEXT_INDEX = 1
    __ITEM_LIST_SEPARATOR = "_"
    __GRAPH_FIELDS = {"node_1", "node_2", "geometry", "length"}

    __OVERPASS_URL = "https://www.overpass-api.de/api/interpreter"
    __OVERPASS_QUERY_PREFIX = "[out:json];"
    # __OVERPASS_QUERY_SUFFIX = ";(._;>;);out geom;"
    __OVERPASS_QUERY_SUFFIX = ""
    __INPUT_EPSG = 4326
    __OUTPUT_EPSG = 3857

    def __init__(self, query):
        super().__init__()

        self._output = []

        self._query = query
        parameters = self._build_parameters()
        self._result_query = self.compute_query(self.__OVERPASS_URL, parameters)
        self.__format_data()
        self.__cleaning_geometry()


    def _build_parameters(self):
        return {"data": f"{self.__OVERPASS_QUERY_PREFIX}{self._query}{self.__OVERPASS_QUERY_SUFFIX}"}

    def __format_data(self):
        self._raw_data = self._result_query["elements"]

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
                try:
                    geometry = ogr_reproject(LineString(line_coordinates), self.__INPUT_EPSG, self.__OUTPUT_EPSG)
                except:
                    geometry = LineString(line_coordinates)

                data = {
                    "node_1": line_coordinates[0],
                    "node_2": line_coordinates[-1],
                    "geometry": geometry,
                    "length": geometry.length,
                }
                data.update(self._get_tags(feature))
                array = np.array(data)

                self._output.append(array)

        if len(self._output) == 0:
            raise ErrorOverpassApi("Data empty")

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

    # def to_graph(self):
    #     self.to_numpy_array()
    #     graph = GraphHelpers(directed=False)
    #
    #     for feature in self._output:
    #         feature_dict = feature.tolist()
    #         graph.add_edge(
    #             str(feature_dict["node_1"]),
    #             str(feature_dict["node_2"]),
    #             f'{str(feature_dict["node_1"])}_{str(feature_dict["node_2"])}',
    #             feature_dict["length"],
    #         )
    #     return graph

    def _get_tags(self, feature):
        return feature.get("tags", {})
