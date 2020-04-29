from scipy import spatial
from scipy.interpolate import interp1d

from shapely.geometry import LineString
from shapely.geometry import Point

import rtree

import numpy as np

import itertools

from collections import Counter

from more_itertools import split_at


class GeomNetworkCleaner:

    __NB_INTERPOLATION_POINTS = 100

    __NUMBER_OF_NODES_INTERSECTIONS = 2
    __NEXT_INDEX = 1
    __ITEM_LIST_SEPARATOR = "_"

    # TODO should be an integer : create a new id ?
    __FIELD_ID = "id"
    __GEOMETRY_FIELD = "geometry"

    def __init__(self, logger, network_data, new_nodes):

        self.logger = logger
        self.logger.info("Network cleaning STARTS!")

        self._network_data = self._check_argument(network_data)
        self._new_nodes = new_nodes

        self._output = []

    def run(self):
        self._prepare_data()

        # connect all the added nodes
        if self._new_nodes is not None:
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
        self.__prepare_tree_analysis()
        line_connection_computed_grouped = self._connect_all_nodes()
        self._rebuild_nearest_connection_intersection(line_connection_computed_grouped)
        self.logger.info("Done: Adding new nodes on the network")

    def __prepare_tree_analysis(self):

        self._network_data_interpolated_line = self.__format_and_interpolate_network_data()
        self._network_data_interpolated_flatten_points = self.__interpolate_network_data_coords_flatten()
        self._network_data_tree = self.__build_kdtree()

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
                self._network_data[nearest_object_id][self.__GEOMETRY_FIELD] = linestring_linked_updated

            # add new lines connection
            for enum, line in enumerate(connection_lines):
                line["id"] = f"{nearest_object_id}_{enum}"
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

    def _connect_all_nodes(self):
        line_connection_computed = []
        for node in self._new_nodes:
            line_connection = self._compute_line_connection(node[self.__GEOMETRY_FIELD])
            del node[self.__GEOMETRY_FIELD]
            if line_connection is not None:
                line_connection.update(node)
                line_connection_computed.append(line_connection)
            else:
                self.logger.info(f"Node '{node[self.__FIELD_ID]}' (id) already exists!")

        line_connection_computed_grouped = self._group_list_of_dict_by_key_value(line_connection_computed, "nearest_object_id")

        return line_connection_computed_grouped

    def _compute_line_connection(self, node):
        dist, nearest_object_idx = self._network_data_tree.query(node)

        nearest_object_id_found = list(self._network_data_interpolated_flatten_points)[nearest_object_idx]
        end_point_on_network = self._network_data_interpolated_flatten_points[nearest_object_id_found]

        connection_coords = [tuple(node), end_point_on_network]
        if frozenset(connection_coords[0]) != (frozenset(connection_coords[-1])):
            line_connection = {
                self.__GEOMETRY_FIELD: connection_coords,
                "nearest_object_id": nearest_object_id_found
            }
            return line_connection

        return None

    def __build_kdtree(self):
        coords_list = list(self._network_data_interpolated_flatten_points.values())
        tree = spatial.KDTree(coords_list)
        return tree

    def __interpolate_network_data_coords_flatten(self):
        network_data_interpolated_flatten_points = {
            f"{feature_id}_{coord_pos}": coord
            for feature_id, feature in self._network_data_interpolated_line.items()
            for coord_pos, coord in enumerate(feature)
        }
        return network_data_interpolated_flatten_points

    def __format_and_interpolate_network_data(self):
        # find the nereast network arc to interpolate
        index = rtree.index.Index()
        for fid, feature in self._network_data.items():
            index.insert(int(fid), feature["bounds"])

        indexes_feature = list(map(str, [
            index_feature
            for node in self._new_nodes
            for index_feature in index.nearest(Point(node[self.__GEOMETRY_FIELD]).bounds, 3)
        ]))

        network_data_interpolated_line = {
            object_id: self.__interpolate_lines(*list(zip(*feature[self.__GEOMETRY_FIELD])))
            for object_id, feature in self._network_data.items()
            if object_id in indexes_feature
        }
        return network_data_interpolated_line

    def __interpolate_lines(self, x_list, y_list):
        interp_func = interp1d(x_list, y_list)

        if len(x_list) > self.__NB_INTERPOLATION_POINTS:
            # means that points road are greater than 100
            # Could be crash here
            self.__NB_INTERPOLATION_POINTS *= 10

        x_new = np.linspace(min(x_list), max(x_list), self.__NB_INTERPOLATION_POINTS - len(x_list) + 2)
        x_new = np.sort(np.append(x_new, x_list[1:-1]))  # include original points
        y_new = interp_func(x_new)
        return list(zip(x_new, y_new))

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
