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

# from osmgt.network.graphtools_helper import GraphHelpers
from osmgt.geometry.reprojection import ogr_reproject

import scipy


class OsmGtCoreError(ValueError):
    pass


class OsmGtCore:

    __NUMBER_OF_NODES_INTERSECTIONS = 2
    __NEXT_INDEX = 1
    __ITEM_LIST_SEPARATOR = "_"
    __GRAPH_FIELDS = {"node_1", "node_2", "geometry", "length"}
    __ID_FIELD = "uuid"

    __INPUT_EPSG = 4326
    __OUTPUT_EPSG = 3857
    __LOCATION_OSM_DEFAULT_ID = 3600000000  # this is it...

    _ways_to_add = []

    def __init__(self, location_name, new_points):
        super().__init__()

        self._location_name = location_name
        self._new_points = new_points

        self._output = []
        self.__get_data_from_osm()
        self.__cleaning_geometry()

    def __get_data_from_osm(self):
        location_id = NominatimApi(q=self._location_name, limit=1).data()[0]["osm_id"]
        location_id += self.__LOCATION_OSM_DEFAULT_ID
        self._raw_data = OverpassApi(location_osm_id=location_id).data()["elements"]

    def __get_all_ways_found_by_query(self):
        all_the_ways_found = filter(lambda x: x["type"] == "way", self._raw_data)
        all_the_ways_found_restructured = {}
        for feature in all_the_ways_found:
            all_the_ways_found_restructured[str(feature["id"])] = feature
            all_the_ways_found_restructured[str(feature["id"])]["geometry"] = [
                [coords["lon"] for coords in feature["geometry"]],
                [coords["lat"] for coords in feature["geometry"]]
            ]
        return all_the_ways_found_restructured

    def __cleaning_geometry(self):
        # find nearest lines from new_points
        all_the_ways_found = self.__get_all_ways_found_by_query()

        for pos, new_node in enumerate(self._new_points):
            all_the_ways_found = self.find_nearest_lines_on_osm_network(all_the_ways_found, new_node, pos)

        # reformat data
        all_the_ways_found = all_the_ways_found.values()

        # find all the existing intersection from coordinates
        intersections_found = self.find_intersections_from_ways(all_the_ways_found)

        for feature in all_the_ways_found:
            coordinates = list(map(frozenset, zip(*feature["geometry"])))
            points_intersections = set(coordinates).intersection(intersections_found)

            lines_coordinates_rebuild = self._topology_builder(coordinates, points_intersections)

            for line_coordinates in lines_coordinates_rebuild:
                line_coordinates = list(map(tuple, line_coordinates))
                # geometry = ogr_reproject(LineString(line_coordinates), self.__INPUT_EPSG, self.__OUTPUT_EPSG)
                geometry = LineString(line_coordinates)
                data = {
                    "node_1": line_coordinates[0],
                    "node_2": line_coordinates[-1],
                    "geometry": geometry,
                    "length": geometry.length,
                    "id": feature["id"]
                }
                data.update(self._get_tags(feature))
                array = np.array(data)

                self._output.append(array)

        self._output = np.stack(self._output)

    def __find_neighbors(self, coords_list):
        from scipy import spatial
        tree = spatial.KDTree(coords_list)
        return tree

    def __interpolate_lines(self, x_list, y_list):
        from scipy.interpolate import interp1d
        interp_func = interp1d(x_list, y_list)
        x_new = np.linspace(min(x_list), max(x_list), 100 - len(x_list) + 2)
        x_new = np.sort(np.append(x_new, x_list[1:-1]))  # include the original points
        y_new = interp_func(x_new)
        return list(zip(x_new, y_new))

    def find_nearest_lines_on_osm_network(self, ways_found, new_node, pos):
        # interpolation lines
        lines_interpolated = {
            str(osm_id): self.__interpolate_lines(
                feature["geometry"][0],
                feature["geometry"][-1]
            )
            for osm_id, feature in ways_found.items()
        }
        all_interpolated_coords_reference = {
            f"{osm_id}_{key}": coord
            for osm_id, feature in lines_interpolated.items()
            for key, coord in enumerate(feature)
        }
        all_interpolated_coords_reference_values = list(all_interpolated_coords_reference.values())

        # find neighbors
        tree = self.__find_neighbors(all_interpolated_coords_reference_values)
        idx_found = tree.query(new_node)[-1]
        osm_id_linked_found = next(key for key, value in all_interpolated_coords_reference.items() if value == all_interpolated_coords_reference_values[idx_found])
        new_feature_coords = {}
        new_feature_coords[osm_id_linked_found] = [
            tuple(new_node),
            all_interpolated_coords_reference_values[idx_found]
        ]
        osm_id, pos_point = osm_id_linked_found.split("_")

        # update geometry
        linestring_linked = ways_found[osm_id]
        linestring_linked_geom_coords = LineString(list(zip(*linestring_linked["geometry"]))).coords[:]
        if len(set(new_feature_coords[osm_id_linked_found]).intersection(set(linestring_linked_geom_coords))) == 1:
            #point found already exists : start or end = nothing to change
            pass
        else:
            line_interpolated = lines_interpolated[osm_id]
            linestring_linked_updated = list(filter(lambda x: x in linestring_linked_geom_coords + [new_feature_coords[osm_id_linked_found][-1]], line_interpolated))
            ways_found[osm_id]["geometry"] = list(zip(*linestring_linked_updated))

        ways_found[f"{osm_id}_{pos}"] = {
            "type": "way",
            "id": f"{osm_id}_{pos}",
            "geometry": list(zip(*new_feature_coords[osm_id_linked_found])),
            "tags": {}  # TODO add attributes ?
        }

        return ways_found

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
            list(map(frozenset, zip(*feature["geometry"])))
            for feature in ways_found
        ]
        intersections_count = Counter([coord for sublist in all_coord_points for coord in sublist])
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
    #         graph.add_edge(
    #             str(feature["node_1"]),
    #             str(feature["node_2"]),
    #             feature["id"],
    #             feature["length"],
    #         )
    #     return graph

    def _get_tags(self, feature):
        return feature.get("tags", {})
