from osmgt.compoments.core import OsmGtCore

from osmgt.apis.overpass import OverpassApi

from osmgt.geometry.network_topology import NetworkTopology

from shapely.geometry import LineString
from shapely.geometry import Point
from shapely.wkt import loads
from osmgt.network.gt_helper import GraphHelpers
import geopandas as gpd
from shapely.geometry import shape

from osmgt.core.global_values import network_queries


class OsmGtRoads(OsmGtCore):

    __DATA_NAME = "network"
    _output_data = None
    __QUERY_MODES = ["vehicle", "pedestrian"]

    def __init__(self):
        super().__init__()

    def from_location(self, location_name, additionnal_nodes=None, mode="vehicle"):
        super().from_location(location_name)
        self._mode = mode

        query = self.get_query_from_mode(mode)
        request = self.from_location_name_query_builder(self._location_id, query)
        raw_data = OverpassApi(self.logger).query(request)["elements"]
        self._output_data = self.__build_network_topology(raw_data, additionnal_nodes, mode)

        return self

    def from_bbox(self, bbox_value, additionnal_nodes=None, mode="vehicle"):
        super().from_bbox(bbox_value)
        self._mode = mode

        query = self.get_query_from_mode(mode)
        request = self.from_bbox_query_builder(bbox_value, query)
        raw_data = OverpassApi(self.logger).query(request)["elements"]
        self._output_data = self.__build_network_topology(raw_data, additionnal_nodes, mode)

        return self

    def from_gdf(self, network_gdf, additionnal_nodes=None, mode="vehicle"):
        # TODO to tests
        raw_data = super().network_from_gdf(network_gdf)
        self._output_data = self.__build_network_topology(raw_data, additionnal_nodes, mode)

        return self

    def get_graph(self):
        self.logger.info("Prepare graph")
        self.check_build_input_data()

        if self._mode == "vehicle":
            graph = GraphHelpers(is_directed=True)
        elif self._mode == "pedestrian":
            graph = GraphHelpers(is_directed=False)

        for feature in self._output_data:
            graph.add_edge(
                Point(feature["geometry"].coords[0]).wkt,
                Point(feature["geometry"].coords[-1]).wkt,
                feature["properties"][self.TOPO_FIELD],
                shape(feature["geometry"]).length,
            )
        return graph

    def __build_network_topology(self, raw_data, additionnal_nodes, mode):

        if additionnal_nodes is not None:
            additionnal_nodes = self.check_topology_field(additionnal_nodes)
            additionnal_nodes = additionnal_nodes.to_dict("records")

        raw_data_restructured = self.__rebuild_network_data(raw_data)
        raw_data_topology_rebuild = NetworkTopology(
            self.logger, raw_data_restructured, additionnal_nodes, self.TOPO_FIELD, mode
        ).run()

        return raw_data_topology_rebuild

    def __rebuild_network_data(self, raw_data):
        self.logger.info("Formating data")

        raw_data = filter(lambda x: x["type"] == "way", raw_data)
        features = []
        for uuid_enum, feature in enumerate(raw_data, start=1):
            geometry = LineString(
                [(coords["lon"], coords["lat"]) for coords in feature["geometry"]]
            )
            del feature["geometry"]

            feature_build = self._build_feature_from_osm(uuid_enum, geometry, feature)
            features.append(feature_build)

        return features

    def get_query_from_mode(self, mode):
        assert mode in network_queries.keys(), f"'{mode}' not found in {', '.join(network_queries.keys())}"
        return network_queries[mode]
