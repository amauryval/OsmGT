from scipy import spatial

from shapely.geometry import LineString

import rtree

import numpy as np

from collections import Counter

from more_itertools import split_at

import functools

import ujson

import concurrent.futures

from itertools import groupby

def deepcopy(variable):
    return ujson.loads(ujson.dumps(variable))


def merge(master, addition):
    overlap_lens = (i + 1 for i, e in enumerate(addition) if e == master[-1])
    for overlap_len in overlap_lens:
        for i in range(overlap_len):
            if master[-overlap_len + i] != addition[i]:
                break
        else:
            return master + addition[overlap_len:]
    return master + addition


class NodesTopology:

    __INTERPOLATION_LEVEL = 7
    __NB_OF_NEAREST_LINE_ELEMENTS_TO_FIND = 5

    __NUMBER_OF_NODES_INTERSECTIONS = 2
    __ITEM_LIST_SEPARATOR_TO_SPLIT_LINE = "_"

    __CLEANING_FILED_STATUS = "topology"

    def __init__(self, logger, network_data, additionnal_nodes, uuid_field):

        self.logger = logger
        self.logger.info("Network cleaning STARTS!")

        self._network_data = self._check_inputs(network_data)

        if uuid_field not in additionnal_nodes.columns.tolist():
            additionnal_nodes[uuid_field] = additionnal_nodes.index.apply(lambda x: int(x))
            print(additionnal_nodes)
        self._additionnal_nodes = ujson.loads(additionnal_nodes.to_json())["features"]
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
            del feature["bounds"]
            self.build_lines(feature)

        return self._output

    def build_lines(self, feature):
        # compare linecoords and intersections points:
        # careful: frozenset destroy the coords order
        # coordinates_list = frozenset(map(frozenset, feature["geometry"]))
        coordinates_list = set(feature["geometry"])
        points_intersections = coordinates_list.intersection(self._intersections_found)

        # rebuild linestring
        if len(set(feature["geometry"])) > 1:
            lines_coordinates_rebuild = self._topology_builder(
                feature["geometry"], points_intersections
            )

            if len(lines_coordinates_rebuild) > 1:

                for new_suffix_id, line_coordinates in enumerate(lines_coordinates_rebuild):
                    feature_updated = deepcopy(feature)
                    feature_updated[self.__FIELD_ID] = str(
                        f"{feature[self.__FIELD_ID]}_{new_suffix_id}"
                    )
                    feature_updated["geometry"] = LineString(line_coordinates)
                    feature_updated[self.__CLEANING_FILED_STATUS] = "split"

                    self._output.append(self._geojson_formating(feature_updated))

            else:
                # nothing to change
                feature["geometry"] = LineString(feature["geometry"])
                feature[self.__FIELD_ID] = str(feature[self.__FIELD_ID])
                self._output.append(self._geojson_formating(feature))

    def _prepare_data(self):

        self._network_data = {
            feature["properties"][self.__FIELD_ID]: {
                **{"geometry": list(map(tuple, feature["geometry"]["coordinates"]))},
                **feature["properties"],
                **{self.__CLEANING_FILED_STATUS: "unchanged"}
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

    def compute_added_node_connections(self):
        self.__node_con_stats = {"connections_added": 0, "line_split": 0}
        self.__connections_added = {}

        self.logger.info("Starting: Adding new nodes on the network")
        node_by_nearest_lines = self.__find_nearest_line_for_each_key_nodes()

        self._bestlines_found = []
        # for node_feature in node_by_nearest_lines.items():
        #     self.proceed_nodes_on_network(node_feature)
        with concurrent.futures.ThreadPoolExecutor(4) as executor:
            executor.map(self.proceed_nodes_on_network, node_by_nearest_lines.items())

        for item in groupby(self._bestlines_found, key=lambda x: x['original_line_key']):
            self.insert_new_nodes_on_its_line(item)

        self._network_data = {**self._network_data, **self.__connections_added}

        stats_infos = ", ".join(
            [f"{key}: {value}" for key, value in self.__node_con_stats.items()]
        )
        self.logger.info(f"Done: Adding new nodes on the network ; {stats_infos}")

    def insert_new_nodes_on_its_line(self, item):
        original_line_key, values = item
        data_to_insert = list(values)

        interpolated_line = [value["interpolated_line"] for value in data_to_insert][0]  # always the same interpolated line...
        end_points_found = list(set([value["end_point_found"] for value in data_to_insert]))  # multiple points can ben found

        linestring_with_new_nodes = self._network_data[original_line_key]["geometry"]
        # self.__node_con_stats["line_split"] += len(end_points_found)
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

        self._network_data[original_line_key]["geometry"] = linestring_linked_updated
        # self._network_data[original_line_key][self.__CLEANING_FILED_STATUS] = "split"

    def proceed_nodes_on_network(self, node_feature):
        node_key, lines_keys = node_feature
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

        if len(set(connection_coords)) > 1:
            # else node_key already on the network, no need to add it on the line
            self.__node_con_stats["connections_added"] += 1
            self._bestlines_found.append(best_line)

        # to split line at node (and also if node is on the network). it builds intersection used to split lines
        self._additionnal_nodes[node_key]["geometry"] = connection_coords
        self._additionnal_nodes[node_key][self.__CLEANING_FILED_STATUS] = "added"
        self._additionnal_nodes[node_key][self.__FIELD_ID] = f"added_{self._additionnal_nodes[node_key][self.__FIELD_ID]}"
        self.__connections_added[f"from_node_id_{node_key}"] = self._additionnal_nodes[node_key]

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
            # map(
            #     frozenset,
                [
                    coords
                    for feature in self._network_data.values()
                    for coords in feature["geometry"]
                ],
            # )
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
                    self.__NB_OF_NEAREST_LINE_ELEMENTS_TO_FIND,
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
