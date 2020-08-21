from osmgt.compoments.core import OsmGtCore

from osmgt.geometry.network_topology import NetworkTopology

from shapely.geometry import LineString
from shapely.geometry import Point

# to facilitate debugging
try:
    from osmgt.network.gt_helper import GraphHelpers
except:
    pass

from shapely.geometry import shape

from osmgt.core.global_values import network_queries


class NetWorkGeomIncompatible(Exception):
    pass


class OsmGtRoads(OsmGtCore):

    _FEATURE_OSM_TYPE = "way"

    def __init__(self):
        super().__init__()

        self._mode = None

    def from_location(self, location_name, additionnal_nodes=None, mode="vehicle"):
        self._check_transport_mode(mode)
        super().from_location(location_name)
        self._mode = mode

        query = self._get_query_from_mode(mode)
        request = self._from_location_name_query_builder(self._location_id, query)
        raw_data = self._query_on_overpass_api(request)
        self._output_data = self.__build_network_topology(
            raw_data, additionnal_nodes, mode
        )

        return self

    def from_bbox(self, bbox_value, additionnal_nodes=None, mode="vehicle"):
        self._check_transport_mode(mode)
        super().from_bbox(bbox_value)
        self._mode = mode

        query = self._get_query_from_mode(mode)
        request = self._from_bbox_query_builder(self._bbox_value, query)
        raw_data = self._query_on_overpass_api(request)
        self._output_data = self.__build_network_topology(
            raw_data, additionnal_nodes, mode
        )

        return self

    def from_gdf(self, network_gdf, additionnal_nodes=None, mode="vehicle"):
        # TODO ? to roads data from others sources
        self._check_transport_mode(mode)
        geometry_found = set(network_gdf[self._GEOMETRY_FIELD].to_list())
        if geometry_found != {"LineString"}:
            raise NetWorkGeomIncompatible(
                f"Input geodataframe does not contains only LineString: {geometry_found}"
            )

        raw_data = super()._build_network_from_gdf(network_gdf)
        self._output_data = self.__build_network_topology(
            raw_data, additionnal_nodes, mode
        )

        return self

    def get_graph(self):
        self.logger.info("Prepare graph")
        self._check_build_input_data()

        graph = GraphHelpers(is_directed=network_queries[self._mode]["directed_graph"])

        for feature in self._output_data:
            graph.add_edge(
                Point(feature[self._GEOMETRY_FIELD].coords[0]).wkt,
                Point(feature[self._GEOMETRY_FIELD].coords[-1]).wkt,
                feature[self._TOPO_FIELD],
                shape(feature[self._GEOMETRY_FIELD]).length,
            )
        return graph

    def __build_network_topology(self, raw_data, additionnal_nodes, mode):
        if additionnal_nodes is not None:
            additionnal_nodes = self._check_topology_field(additionnal_nodes)
            # filter nodes from study_area_geom
            additionnal_nodes_mask = additionnal_nodes.intersects(self.study_area_geom)
            additionnal_nodes = additionnal_nodes.loc[additionnal_nodes_mask]
            additionnal_nodes = additionnal_nodes.to_dict("records")

        raw_data_restructured = self.__rebuild_network_data(raw_data)
        raw_data_topology_rebuild = NetworkTopology(
            self.logger,
            raw_data_restructured,
            additionnal_nodes,
            self._TOPO_FIELD,
            mode,
        ).run()

        return raw_data_topology_rebuild

    def __rebuild_network_data(self, raw_data):
        self.logger.info("Formating data")

        raw_data = filter(
            lambda x: x[self._FEATURE_TYPE_OSM_FIELD] == self._FEATURE_OSM_TYPE,
            raw_data,
        )
        features = []
        for uuid_enum, feature in enumerate(raw_data, start=1):
            geometry = LineString(
                [
                    (coords[self._LNG_FIELD], coords[self._LAT_FIELD])
                    for coords in feature[self._GEOMETRY_FIELD]
                ]
            )
            del feature[self._GEOMETRY_FIELD]

            feature_build = self._build_feature_from_osm(uuid_enum, geometry, feature)
            features.append(feature_build)

        return features

    @staticmethod
    def _get_query_from_mode(mode):
        return network_queries[mode]["query"]
