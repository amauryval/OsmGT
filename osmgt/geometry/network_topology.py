from scipy import spatial

from shapely.geometry import Point
from shapely.geometry import LineString

import rtree

import numpy as np

from collections import Counter

from more_itertools import split_at

import functools

import ujson

from numba import jit
from numba import types as nb_types

import concurrent.futures


def deepcopy(variable):
    return ujson.loads(ujson.dumps(variable))


class NetworkTopology:
    # TODO return topology stats
    # TODO oneway field to arg

    __INTERPOLATION_LEVEL = 7
    __NB_OF_NEAREST_LINE_ELEMENTS_TO_FIND = 10

    __NUMBER_OF_NODES_INTERSECTIONS = 2
    __ITEM_LIST_SEPARATOR_TO_SPLIT_LINE = "_"

    __CLEANING_FILED_STATUS = "topology"
    __GEOMETRY_FIELD = "geometry"
    __COORDINATES_FIELD = "coordinates"
    __ONEWAY_FIELD = "oneway"

    def __init__(self, logger, network_data, additionnal_nodes, uuid_field, mode_post_processing):
        """

        :param logger:
        :type network_data: list of dict
        :type additionnal_nodes: list of dict
        :type uuid_field: str
        :type mode_post_processing: str
        """
        self.logger = logger
        self.logger.info("Network cleaning STARTS!")

        self._network_data = self._check_inputs(network_data)
        self._additionnal_nodes = additionnal_nodes
        self._mode_post_processing = mode_post_processing

        self.__FIELD_ID = uuid_field  # have to be an integer.. thank rtree...

        self._output = []

    def run(self):
        self._prepare_data()

        # connect all the added nodes
        if self._additionnal_nodes is not None:
            self.compute_added_node_connections()

        # find all the existing intersection from coordinates
        self._intersections_found = set(self.find_intersections_from_ways())

        self.logger.info("Starting: build lines")
        for feature in self._network_data.values():
            self.build_lines(feature)

        return self._output

    def build_lines(self, feature):
        # del feature["bounds"]  # useless now
        del feature[self.__GEOMETRY_FIELD]  # useless now

        # compare linecoords and intersections points
        coordinates_list = set(feature[self.__COORDINATES_FIELD])
        points_intersections = coordinates_list.intersection(self._intersections_found)

        # rebuild linestring
        if len(set(feature[self.__COORDINATES_FIELD])) > 1:
            lines_coordinates_rebuild = self._topology_builder(
                feature[self.__COORDINATES_FIELD], points_intersections
            )

            if len(lines_coordinates_rebuild) > 1:

                for new_suffix_id, line_coordinates in enumerate(lines_coordinates_rebuild):
                    feature_updated = deepcopy(feature)
                    feature_updated[self.__FIELD_ID] = f"{feature_updated[self.__FIELD_ID]}_{new_suffix_id}"
                    feature_updated[self.__CLEANING_FILED_STATUS] = "split"
                    feature_updated[self.__COORDINATES_FIELD] = line_coordinates

                    new_features = self.mode_processing(feature_updated)
                    self._output.extend(new_features)
            else:
                # nothing to change
                feature[self.__FIELD_ID] = f"{feature[self.__FIELD_ID]}"
                new_features = self.mode_processing(feature)
                self._output.extend(new_features)

    def mode_processing(self, input_feature):
        new_elements = []

        if self._mode_post_processing == "vehicle":
            # by default
            new_forward_feature = self._direction_processing(input_feature, "forward")
            new_elements.append(new_forward_feature)
            if input_feature.get("junction", None) in ["roundabout", "jughandle"]:
                return new_elements

            if input_feature.get(self.__ONEWAY_FIELD, None) != "yes":
                new_backward_feature = self._direction_processing(input_feature, "backward")
                new_elements.append(new_backward_feature)

        elif self._mode_post_processing == "pedestrian":
            # it's the default behavior in fact

            feature = self._direction_processing(input_feature)
            new_elements.append(feature)

        return new_elements

    def _direction_processing(self, input_feature, direction=None):
        feature = deepcopy(input_feature)
        if direction == "backward":
            feature[self.__GEOMETRY_FIELD] = LineString(feature[self.__COORDINATES_FIELD][::-1])
        elif direction in ["forward", None]:
            feature[self.__GEOMETRY_FIELD] = LineString(feature[self.__COORDINATES_FIELD])

        if direction is not None:
            feature[self.__FIELD_ID] = f"{feature[self.__FIELD_ID]}_{direction}"
        else:
            feature[self.__FIELD_ID] = f"{feature[self.__FIELD_ID]}"

        del feature[self.__COORDINATES_FIELD]
        return feature

    def _prepare_data(self):

        self._network_data = {
            feature[self.__FIELD_ID]: {
                **{self.__COORDINATES_FIELD: feature[self.__GEOMETRY_FIELD].coords[:]},
                **feature,
                **{self.__CLEANING_FILED_STATUS: "unchanged"}
            }
            for feature in self._network_data
        }
        if self._additionnal_nodes is not None:
            self._additionnal_nodes = {
                feature[self.__FIELD_ID]: {
                    **{self.__COORDINATES_FIELD: feature[self.__GEOMETRY_FIELD].coords[0]},
                    **feature,
                }
                for feature in self._additionnal_nodes
            }

    def compute_added_node_connections(self):
        self.logger.info("Starting: Adding new nodes on the network")
        self.__node_con_stats = {"connections_added": 0, "line_split": 0}
        self.__connections_added = {}

        self.logger.info("Find nearest line for each node")
        nearest_line_and_its_nodes = self.__find_nearest_line_for_each_key_nodes()

        self.logger.info("Split line")
        self._bestlines_found = []
        for nearest_line_content in nearest_line_and_its_nodes.items():
            default_line_updater = self.proceed_nodes_on_network(nearest_line_content)
            if default_line_updater is not None:
                self.insert_new_nodes_on_its_line(default_line_updater)
        # with concurrent.futures.ThreadPoolExecutor(4) as executor:
        #     executor.map(self.proceed_nodes_on_network, nearest_line_and_its_nodes.items())


        self._network_data = {**self._network_data, **self.__connections_added}

        stats_infos = ", ".join(
            [f"{key}: {value}" for key, value in self.__node_con_stats.items()]
        )
        self.logger.info(f"Done: Adding new nodes on the network ; {stats_infos}")

    def insert_new_nodes_on_its_line(self, item):
        original_line_key = item["original_line_key"]
        interpolated_line = item["interpolated_line"]
        end_points_found = item["end_points_found"]

        linestring_with_new_nodes = self._network_data[original_line_key][self.__COORDINATES_FIELD]
        linestring_with_new_nodes.extend(end_points_found)
        linestring_with_new_nodes = set(linestring_with_new_nodes)
        self.__node_con_stats["line_split"] += len(linestring_with_new_nodes.intersection(end_points_found))

        # build new linestrings
        linestring_linked_updated = list(
            filter(
                lambda x: x in linestring_with_new_nodes,
                interpolated_line,
            )
        )

        self._network_data[original_line_key][self.__COORDINATES_FIELD] = linestring_linked_updated

    def proceed_nodes_on_network(self, nearest_line_content):
        nearest_line_key, node_keys = nearest_line_content

        # interpolated_line_coords = self.__compute_interpolation_on_line(nearest_line_key, self.__INTERPOLATION_LEVEL)
        interpolated_line_coords = interpolate_curve_based_on_original_points(
            np.array(self._network_data[nearest_line_key][self.__COORDINATES_FIELD]),
            self.__INTERPOLATION_LEVEL
        )
        line_tree = spatial.cKDTree(interpolated_line_coords)
        interpolated_line_coords_reformated = list(map(tuple, interpolated_line_coords))

        default_line_updater = {
            "interpolated_line": interpolated_line_coords_reformated,
            "original_line_key": nearest_line_key,
            "end_points_found": None
        }

        nodes_coords = [self._additionnal_nodes[node_key]["coordinates"] for node_key in node_keys]
        _, nearest_line_object_idxes = line_tree.query(nodes_coords)
        end_points_found = [interpolated_line_coords_reformated[nearest_line_key] for nearest_line_key in nearest_line_object_idxes]
        default_line_updater["end_points_found"] = end_points_found

        connections_coords = list(
            zip(
                node_keys,
                list(zip(nodes_coords, end_points_found))
            )
        )
        self.__node_con_stats["connections_added"] += len(connections_coords)

        connections_coords_valid = list(filter(lambda x: len(set(x[-1])) > 0, connections_coords))
        for node_key, connection in connections_coords_valid:

            # to split line at node (and also if node is on the network). it builds intersection used to split lines
            # additionnal are converted to lines
            self._additionnal_nodes[node_key][self.__COORDINATES_FIELD] = connection
            self._additionnal_nodes[node_key][self.__CLEANING_FILED_STATUS] = "added"
            self._additionnal_nodes[node_key][self.__FIELD_ID] = f"added_{self._additionnal_nodes[node_key][self.__FIELD_ID]}"

            self.__connections_added[f"from_node_id_{node_key}"] = self._additionnal_nodes[node_key]

        if default_line_updater["end_points_found"] is not None:
            return default_line_updater

        return None

    def _topology_builder(self, coordinates, points_intersections):

        is_rebuild = False

        # split coordinates found at intersection to respect the topology
        first_value, *middle_coordinates_values, last_value = coordinates
        for point_intersection in points_intersections:

            point_intersection = tuple(point_intersection)

            if point_intersection in middle_coordinates_values:
                # we get the middle values from coordinates to avoid to catch the first and last value when editing

                middle_coordinates_values = self._insert_value(
                    middle_coordinates_values, point_intersection, tuple([point_intersection])
                )

                middle_coordinates_values = self._insert_value(
                    middle_coordinates_values,
                    point_intersection,
                    self.__ITEM_LIST_SEPARATOR_TO_SPLIT_LINE,
                    "after",
                )
                coordinates = [first_value] + middle_coordinates_values + [last_value]
                is_rebuild = True

        if is_rebuild:
            coordinates_upd = list(split_at(coordinates, lambda x: x == "_"))

        if not is_rebuild:
            coordinates_upd = list([coordinates])

        return coordinates_upd

    def find_intersections_from_ways(self):
        self.logger.info("Starting: Find intersections")
        all_coord_points = Counter(
            [
                coords
                for feature in self._network_data.values()
                for coords in feature[self.__COORDINATES_FIELD]
            ],
        )

        intersections_found = dict(
            filter(
                lambda x: x[1] >= self.__NUMBER_OF_NODES_INTERSECTIONS,
                all_coord_points.items(),
            )
        ).keys()
        self.logger.info("Done: Find intersections")

        return set(intersections_found)

    def __find_nearest_line_for_each_key_nodes(self):
        # find the nereast network arc to interpolate
        self.__tree_index = rtree.index.Index()
        for fid, feature in self._network_data.items():
            self.__tree_index.insert(
                int(fid), feature[self.__GEOMETRY_FIELD].bounds
            )

        # find nearest line
        self.__node_by_nearest_lines = {}
        for node_info in self._additionnal_nodes.items():
            self.__get_nearest_line(node_info)

        return self.__node_by_nearest_lines

    def __get_nearest_line(self, node_info):
        node_uuid , node = node_info
        distances_computed = []
        node_geom = Point(node[self.__GEOMETRY_FIELD])
        for index_feature in self.__tree_index.nearest(node[self.__GEOMETRY_FIELD].bounds, self.__NB_OF_NEAREST_LINE_ELEMENTS_TO_FIND):

            line_geom = LineString(self._network_data[index_feature][self.__COORDINATES_FIELD])
            distance_from_node_to_line = node_geom.distance(line_geom)
            distances_computed.append((distance_from_node_to_line , index_feature))
            if distance_from_node_to_line == 0:
                # means that we node is on the network, looping is not necessary anymore
                break

        _, line_min_index = min(distances_computed)
        if line_min_index not in self.__node_by_nearest_lines:
            self.__node_by_nearest_lines[line_min_index] = [node_uuid]
        else:
            self.__node_by_nearest_lines[line_min_index].append(node_uuid)

    @staticmethod
    def find_nearest_geometry(point, geometries):
        min_dist , min_index = (
            min(
                (point.distance(geom), k)
                for (k , geom) in enumerate(geometries)
            )
        )

        return geometries[min_index] , min_dist , min_index

    def _check_inputs(self, inputs):
        # TODO add assert
        assert len(inputs) > 0
        return inputs

    @staticmethod
    def _insert_value(list_object, search_value, value_to_add, position=None):
        assert position in {None, "after", "before"}

        index_increment = 0
        if position == "before":
            index_increment = -1
        elif position == "after":
            index_increment = 1

        index = list_object.index(search_value) + index_increment
        list_object[index:index] = value_to_add

        return list_object

    def _geojson_formating(self, input_data):
        properties_fields = list(input_data.keys())
        properties_fields.remove("geometry")
        geometry, properties = map(lambda keys: {x: input_data[x] for x in keys} , [[self.__COORDINATES_FIELD], properties_fields])
        return {**geometry, "properties": properties}

    @functools.lru_cache(maxsize=2097152)
    def __compute_interpolation_on_line(self, line_key_found, interpolation_level):

        interpolated_line_coords = interpolate_curve_based_on_original_points(
            np.array(self._network_data[line_key_found][self.__COORDINATES_FIELD]), interpolation_level
        )

        return interpolated_line_coords

# @jit(nopython=True, nogil=True, cache=True)
def compute_interpolation_on_line(line_found, interpolation_level):

    interpolated_line_coords = interpolate_curve_based_on_original_points(
        line_found, interpolation_level
    )

    return interpolated_line_coords

signature_interpolation_func = nb_types.Array(nb_types.float64, 2, 'C')(nb_types.Array(nb_types.float64, 2, 'C'), nb_types.int64)
@jit(signature_interpolation_func, nopython=True, nogil=True, cache=True)
def interpolate_curve_based_on_original_points(x, n):
    # source https://stackoverflow.com/questions/31243002/higher-order-local-interpolation-of-implicit-curves-in-python/31335255
    if n > 1:
        m = 0.5 * (x[:-1] + x[1:])
        if x.ndim == 2:
            msize = (x.shape[0] + m.shape[0], x.shape[1])
        else:
            raise NotImplementedError
        x_new = np.empty(msize, dtype=x.dtype)
        x_new[0::2] = x
        x_new[1::2] = m
        return interpolate_curve_based_on_original_points(x_new, n - 1)

    elif n == 1:
        return x

    else:
        raise ValueError
