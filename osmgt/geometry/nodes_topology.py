from scipy import spatial

from shapely.geometry import LineString

import rtree

import numpy as np

from collections import Counter

from more_itertools import split_at

import functools

import copy


class GeomNetworkCleaner:

    __INTERPOLATION_LEVEL = 7
    __NB_OF_NEAREST_ELEMENTS_TO_FIND = 5

    __NUMBER_OF_NODES_INTERSECTIONS = 2
    __ITEM_LIST_SEPARATOR_TO_SPLIT_LINE = "_"

    __FIELD_ID = "uuid"

    def __init__(self, logger, network_data, additionnal_nodes):

        self.logger = logger
        self.logger.info("Network cleaning STARTS!")

        self._network_data = self._check_inputs(network_data)
        self._additionnal_nodes = additionnal_nodes.__geo_interface__["features"]

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
            # careful: frozenset destroy the coords order
            coordinates_list = frozenset(map(frozenset, feature["geometry"]))
            points_intersections = coordinates_list.intersection(intersections_found)

            # rebuild linestring
            lines_coordinates_rebuild = self._topology_builder(
                feature["geometry"], points_intersections
            )

            if len(lines_coordinates_rebuild) != 0:
                for new_suffix_id, line_coordinates in enumerate(
                    lines_coordinates_rebuild
                ):

                    new_geometry = LineString(line_coordinates)
                    new_geometry_length = new_geometry.length
                    if new_geometry_length > 0:

                        feature_updated = copy.deepcopy(feature)
                        feature_updated["uuid"] = str(
                            f"{feature['id']}_{new_suffix_id}"
                        )
                        feature_updated["geometry"] = new_geometry
                        feature_updated["bounds"] = ", ".join(
                            map(str, new_geometry.bounds)
                        )
                        feature_updated["length"] = new_geometry_length

                        self._output.append(self._geojson_formating(feature_updated))

            else:
                assert set(feature["geometry"]) == set(lines_coordinates_rebuild[0])
                # nothing to change
                feature["geometry"] = LineString(feature["geometry"])
                feature["length"] = feature["geometry"].length
                self._output.append(self._geojson_formating(feature))

        return self._output

    def _prepare_data(self):
        self._network_data = {
            feature["properties"][self.__FIELD_ID]: {
                **{"geometry": list(map(tuple, feature["geometry"]["coordinates"]))},
                **feature["properties"],
            }
            for feature in self._network_data
        }

        self._additionnal_nodes = {
            feature["properties"][self.__FIELD_ID]: {
                **{"geometry": feature["geometry"]["coordinates"]},
                **feature["properties"],
            }
            for feature in self._additionnal_nodes
        }
        assert True

    def compute_added_node_connections(self):
        node_con_stats = {"connections_added": 0, "line_split": 0}
        connections_added = {}

        self.logger.info("Starting: Adding new nodes on the network")
        node_by_nearest_lines = self.__find_nearest_line_for_each_key_nodes()

        for node_key, lines_keys in node_by_nearest_lines.items():
            node_found = self._additionnal_nodes[node_key]
            candidates = {}
            for line_key in lines_keys:
                interpolated_line_coords = self.__compute_interpolation_on_line(
                    line_key
                )

                line_tree = spatial.cKDTree(interpolated_line_coords)
                dist, nearest_line_object_idx = line_tree.query(node_found["geometry"])

                new_candidate = {
                    "interpolated_line": list(map(tuple, interpolated_line_coords)),
                    "original_line": self._network_data[line_key]["geometry"],
                    "original_line_key": line_key,
                    "end_point_found": tuple(
                        interpolated_line_coords[nearest_line_object_idx]
                    ),
                }
                candidates[dist] = new_candidate

            best_line = candidates[min(candidates.keys())]
            connection_coords = [
                tuple(node_found["geometry"]),
                best_line["end_point_found"],
            ]

            if frozenset(connection_coords[0]) != (frozenset(connection_coords[-1])):
                # update source node geom
                self._additionnal_nodes[node_key]["geometry"] = connection_coords
                connections_added[f"from_node_id_{node_key}"] = self._additionnal_nodes[
                    node_key
                ]
                node_con_stats["connections_added"] += 1
            else:
                # node_key already on the network, no need to add it on the graph ; line is not split

                # TODO ? here trying to force split line if node is on the network
                self._additionnal_nodes[node_key]["geometry"] = connection_coords
                connections_added[f"from_node_id_{node_key}"] = self._additionnal_nodes[
                    node_key
                ]

            # update source line geom
            linestring_linked_updated = list(
                filter(
                    lambda x: tuple(x)
                    in best_line["original_line"] + [best_line["end_point_found"]],
                    best_line["interpolated_line"],
                )
            )

            if len(linestring_linked_updated) == 1:
                print(f"no need to update line, because no new node added")
            if len(linestring_linked_updated) == 0:
                assert True
            else:
                node_con_stats["line_split"] += 1
                self._network_data[best_line["original_line_key"]][
                    "geometry"
                ] = linestring_linked_updated

        self._network_data = {**self._network_data, **connections_added}

        stats_infos = ", ".join(
            [f"{key}: {value}" for key, value in node_con_stats.items()]
        )
        self.logger.info(f"Done: Adding new nodes on the network ; {stats_infos}")

    @functools.lru_cache(maxsize=None)
    def __compute_interpolation_on_line(self, line_key):

        line_found = self._network_data[line_key]
        interpolated_line_coords = interpolate_curve_based_on_original_points(
            np.vstack(list(zip(*line_found["geometry"]))).T, self.__INTERPOLATION_LEVEL
        ).tolist()

        return interpolated_line_coords

    def _topology_builder(self, coordinates, points_intersections):
        is_rebuild = False

        # split coordinates found at intersection to respect the topology
        first_value, *middle_coordinates_values, last_value = coordinates
        for point_intersection in points_intersections:

            point_intersection = tuple(point_intersection)
            if point_intersection in middle_coordinates_values:
                # we get the middle values from coordinates to avoid to catch the first and last value when editing

                middle_coordinates_values = self._insert_value(
                    middle_coordinates_values, point_intersection, point_intersection
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
            map(
                frozenset,
                [
                    coords
                    for feature in self._network_data.values()
                    for coords in feature["geometry"]
                ],
            )
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
        tree_index = rtree.index.Index()
        for fid, feature in self._network_data.items():
            tree_index.insert(
                int(fid), tuple(map(float, feature["bounds"].split(", ")))
            )

        node_by_nearest_lines = {
            node_uuid: [
                index_feature
                for index_feature in tree_index.nearest(
                    tuple(map(float, node["bounds"].split(", "))),
                    self.__NB_OF_NEAREST_ELEMENTS_TO_FIND,
                )
            ]
            for node_uuid, node in self._additionnal_nodes.items()
        }

        return node_by_nearest_lines

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
        if position == "after":
            index_increment = 1

        try:
            list_object.insert(
                list_object.index(search_value) + index_increment, value_to_add
            )
            return list_object
        except ValueError:
            raise ValueError(f"{search_value} not found")

    def _geojson_formating(self, input_data):
        geometry = input_data["geometry"]
        del input_data["geometry"]
        properties = input_data
        return {"geometry": geometry, "properties": properties}


def interpolate_curve_based_on_original_points(x, n):
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
