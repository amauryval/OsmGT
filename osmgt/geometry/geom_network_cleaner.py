from scipy import spatial
from scipy.interpolate import interp1d, splev

from shapely.geometry import LineString
from shapely.geometry import Point

import rtree

import numpy as np

import itertools

from collections import Counter

from more_itertools import split_at

import sys
sys.setrecursionlimit(10000)

class GeomNetworkCleaner:

    __NB_INTERPOLATION_POINTS = 100
    __INTERPOLATION_LEVEL = 7

    __NUMBER_OF_NODES_INTERSECTIONS = 2
    __NEXT_INDEX = 1
    __ITEM_LIST_SEPARATOR = "_"

    # TODO should be an integer : create a new id ?
    __FIELD_ID = "id"
    __GEOMETRY_FIELD = "geometry"

    def __init__(self, logger, network_data, additionnal_nodes):

        self.logger = logger
        self.logger.info("Network cleaning STARTS!")

        self._network_data = self._check_argument(network_data)
        self._additionnal_nodes = additionnal_nodes

        self._output = []

    def run(self):
        self._prepare_data()

        # connect all the added nodes
        if self._additionnal_nodes is not None:
            self.compute_added_node_connections()

        # find all the existing intersection from coordinates
        intersections_found = self.find_intersections_from_ways()

        self.logger.info("Starting: build lines")
        for feature in self._network_data.values():

            # compare linecoords and intersections points:
            coordinates_list = frozenset(map(frozenset, feature[self.__GEOMETRY_FIELD]))  # careful: frozenset destroy the coords order
            points_intersections = coordinates_list.intersection(intersections_found)

            # rebuild linestring
            lines_coordinates_rebuild = self._topology_builder(feature[self.__GEOMETRY_FIELD], points_intersections)

            for new_suffix_id, line_coordinates in enumerate(lines_coordinates_rebuild):
                geometry = LineString(line_coordinates)
                data = {
                    "node_1": line_coordinates[0],
                    "node_2": line_coordinates[-1],
                    "geometry": geometry,
                    "length": geometry.length,
                    self.__FIELD_ID: f"{feature[self.__FIELD_ID]}_{new_suffix_id}"
                }
                data.update(self._get_tags(feature))

                self._output.append(np.array(data))

        self.logger.info("Done: build lines")
        self.logger.info("Network cleaning DONE!")

        return np.stack(self._output)

    def _prepare_data(self):
        self._network_data = {
            str(feature[self.__FIELD_ID]): feature
            for feature in self._network_data
        }

    def compute_added_node_connections(self):

        self.logger.info("Starting: Adding new nodes on the network")
        node_by_nearest_lines = self.__find_nearest_line_for_each_key_nodes()

        for node_key, lines_keys in node_by_nearest_lines.items():
            node_found = self._additionnal_nodes[node_key]

            candidates = {}
            for line_key in lines_keys:
                line_found = self._network_data[line_key]
                interpolated_line_coords = self.__interpolate_curve_from_original_points(
                    np.vstack(list(zip(*line_found["geometry"]))).T,
                    self.__INTERPOLATION_LEVEL
                ).tolist()
                line_tree = spatial.cKDTree(interpolated_line_coords)
                dist, nearest_line_object_idx = line_tree.query(node_found["geometry"])
                candidates[dist] = {
                    "interpolated_line": list(map(tuple, interpolated_line_coords)),
                    "original_line": line_found["geometry"],
                    "original_line_key": line_key,
                    "end_point_found": tuple(interpolated_line_coords[nearest_line_object_idx])
                }

            best_line = candidates[min(candidates.keys())]
            connection_coords = [tuple(node_found["geometry"]), best_line["end_point_found"]]

            if frozenset(connection_coords[0]) != (frozenset(connection_coords[-1])):
                # update source node geom
                self._additionnal_nodes[node_key]["geometry"] = connection_coords
                self._network_data[f"from_node_id_{node_key}"] = self._additionnal_nodes[node_key]
            else:
                print(f"{node_key} already on the network")

            #update source line geom
            linestring_linked_updated = list(
                filter(
                    lambda x: tuple(x) in best_line["original_line"] + [best_line["end_point_found"]],
                    best_line["interpolated_line"]
                )
            )
            if len(linestring_linked_updated) == 1:
                print(f"no need to update line, because no new node added")
            if len(linestring_linked_updated) == 0:
                assert True
            else:
                self._network_data[best_line["original_line_key"]]["geometry"] = linestring_linked_updated

        self.logger.info("Done: Adding new nodes on the network")

    def _rebuild_nearest_connection_intersection(self, line_connection_computed_grouped):
        # rebuild nearest geometry
        for nearest_object_id, connection_lines in line_connection_computed_grouped.items():
            end_points_to_add_nearest_object = [
                line_coord[self.__GEOMETRY_FIELD][-1]
                for line_coord in connection_lines
            ]
            # get original geometry
            original_linestring_linked_coords = self._network_data[nearest_object_id][self.__GEOMETRY_FIELD]

            nodes_intersections = set(end_points_to_add_nearest_object).intersection(set(original_linestring_linked_coords))
            if len(nodes_intersections) == len(end_points_to_add_nearest_object):
                # point found already exists : start or end = nothing to change
                pass
            else:
                line_interpolated = self._network_data_interpolated_line[nearest_object_id]
                linestring_linked_updated = list(
                    filter(
                        lambda x: x in original_linestring_linked_coords + end_points_to_add_nearest_object,
                        line_interpolated
                    )
                )
                if len(linestring_linked_updated) == 1:
                    assert True
                self._network_data[nearest_object_id][self.__GEOMETRY_FIELD] = linestring_linked_updated

            # add new lines connection
            for enum, line in enumerate(connection_lines):
                line["id"] = f"{nearest_object_id}_{enum}"
                if len(linestring_linked_updated) == 1:
                    assert True
                line[self.__GEOMETRY_FIELD] = line[self.__GEOMETRY_FIELD]
                self._network_data[line["id"]] = line

    def _topology_builder(self, coordinates, points_intersections):
        is_rebuild = False

        # split coordinates found at intersection to respect the topology
        first_value, *middle_coordinates_values, last_value = coordinates
        for point_intersection in points_intersections:

            point_intersection = tuple(point_intersection)
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
            coordinates_upd = list(split_at(coordinates, lambda x: x == '_'))

        if not is_rebuild:
            coordinates_upd = list([coordinates])

        return coordinates_upd

    def find_intersections_from_ways(self):
        self.logger.info("Starting: Find intersections")
        all_coord_points = Counter(map(
            frozenset,
            [
                coords
                for feature in self._network_data.values()
                for coords in feature[self.__GEOMETRY_FIELD]
            ]
        ))
        intersections_found = dict(filter(lambda x: x[1] >= self.__NUMBER_OF_NODES_INTERSECTIONS, all_coord_points.items())).keys()
        self.logger.info("Done: Find intersections")

        return set(intersections_found)

    def __find_nearest_line_for_each_key_nodes(self):
        # find the nereast network arc to interpolate
        index = rtree.index.Index()
        for fid, feature in self._network_data.items():
            index.insert(int(fid), feature["bounds"])

        node_by_nearest_lines = {
            str(node_uuid): [
                str(index_feature)
                for index_feature in index.nearest(Point(node[self.__GEOMETRY_FIELD]).bounds, 3)
            ]
            for node_uuid, node in self._additionnal_nodes.items()
        }

        # line_key_by_node_keys = {
        #     line_value: [
        #         node_key
        #         for node_key in node_by_nearest_linestring.keys()
        #         if node_by_nearest_linestring[node_key] == line_value
        #     ]
        #     for line_value in set(node_by_nearest_linestring.values())
        # }

        return node_by_nearest_lines

    def __interpolate_curve_from_original_points(self, x, n):
        if n > 1:
            m = 0.5 * (x[:-1] + x[1:])
            if x.ndim == 2:
                msize = (x.shape[0] + m.shape[0], x.shape[1])
            else:
                raise NotImplementedError
            x_new = np.empty(msize, dtype=x.dtype)
            x_new[0::2] = x
            x_new[1::2] = m
            return self.__interpolate_curve_from_original_points(x_new, n - 1)
        elif n == 1:
            return x
        else:
            raise ValueError

    def __interpolate_lines_from_original_points(self, x_list, y_list):
        interp_func = interp1d(x_list, y_list)

        if len(x_list) > self.__NB_INTERPOLATION_POINTS:
            # means that points road are greater than 100
            # Could be crash here
            self.__NB_INTERPOLATION_POINTS *= 10

        x_new = np.linspace(min(x_list), max(x_list), self.__NB_INTERPOLATION_POINTS - len(x_list) + 2)
        x_new = np.sort(np.append(x_new, x_list[1:-1]))  # include original points
        y_new = interp_func(x_new)
        return list(zip(x_new, y_new))

    def __interpolate_lines_from_distance(self, x_list, y_list):
        points = np.array([x_list, y_list]).T  # a (nbre_points x nbre_dim) array

        # Linear length along the line:
        distance = np.cumsum(np.sqrt(np.sum(np.diff(points, axis=0) ** 2, axis=1)))
        distance = np.insert(distance, 0, 0) / distance[-1]

        # Interpolation for different methods:
        alpha = np.linspace(distance.min(), int(distance.max()), 10)

        interpolator = interp1d(distance, points, kind="slinear", axis=0)
        new_points = interpolator(alpha)
        a = list(map(tuple, new_points.tolist()))
        if len(a) == 1:
            assert True
        return list(map(tuple, new_points.tolist()))

    def _check_argument(self, argument):
        # TODO check argument
        return argument

    def _group_list_of_dict_by_key_value(self, dict_object, key_name):
        return {
            key: [value for value in dict_object if value[key_name].split("_")[0] == key]
            for key, _ in itertools.groupby(dict_object, lambda x: x[key_name].split("_")[0])
        }

    def _get_tags(self, feature):
        return feature.get("tags", {})
