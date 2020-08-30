import geopandas as gpd
from typing import Tuple
from typing import List
from typing import Optional
from typing import Dict
from typing import Iterator


from osmgt.compoments.core import OsmGtCore

from osmgt.geometry.network_topology import NetworkTopology
from osmgt.geometry.geom_helpers import compute_wg84_line_length

from shapely.geometry import LineString
from shapely.geometry import Point

# to facilitate debugging
try:
    from osmgt.network.gt_helper import GraphHelpers
except ModuleNotFoundError:
    pass

from shapely.geometry import shape

from osmgt.core.global_values import network_queries


class NetWorkGeomIncompatible(Exception):
    pass


class AdditionnalNodesOutsideWorkingArea(Exception):
    pass


class OsmGtRoads(OsmGtCore):

    _FEATURE_OSM_TYPE: str = "way"

    def __init__(self) -> None:
        super().__init__()

        self._mode = None

    def from_location(
        self,
        location_name: str,
        additionnal_nodes: Optional[gpd.GeoDataFrame],
        mode: str,
    ) -> None:
        self._check_transport_mode(mode)
        super().from_location(location_name)
        self._mode = mode

        query = self._get_query_from_mode(mode)
        request = self._from_location_name_query_builder(self._location_id, query)
        raw_data = self._query_on_overpass_api(request)
        self._output_data = self.__build_network_topology(
            raw_data, additionnal_nodes, mode
        )

    def from_bbox(
        self,
        bbox_value: Tuple[float, float, float, float],
        additionnal_nodes: Optional[gpd.GeoDataFrame],
        mode: str,
    ) -> None:
        self._check_transport_mode(mode)
        super().from_bbox(bbox_value)
        self._mode = mode

        query = self._get_query_from_mode(mode)
        request = self._from_bbox_query_builder(self._bbox_value, query)
        raw_data = self._query_on_overpass_api(request)
        self._output_data = self.__build_network_topology(
            raw_data, additionnal_nodes, mode
        )

    def get_graph(self) -> GraphHelpers:
        self.logger.info("Prepare graph")
        self._check_build_input_data()

        graph = GraphHelpers(
            self.logger, is_directed=network_queries[self._mode]["directed_graph"]
        )

        for feature in self._output_data:
            graph.add_edge(*self.__compute_edges(feature))

        return graph

    def __compute_edges(self, feature: Dict) -> Tuple[str, str, str, float]:
        coordinates = feature[self._GEOMETRY_FIELD]
        return (
            Point(coordinates.coords[0]).wkt,
            Point(coordinates.coords[-1]).wkt,
            feature[self._TOPO_FIELD],
            compute_wg84_line_length(shape(coordinates)),
        )

    def __build_network_topology(
        self,
        raw_data: List[Dict],
        additionnal_nodes: Optional[gpd.GeoDataFrame],
        mode: str,
    ) -> List[Dict]:
        if additionnal_nodes is not None:
            additionnal_nodes = self._check_topology_field(additionnal_nodes)
            # filter nodes from study_area_geom
            additionnal_nodes_mask = additionnal_nodes.intersects(self.study_area_geom)
            additionnal_nodes_filtered = additionnal_nodes.loc[additionnal_nodes_mask]

            if additionnal_nodes_filtered.shape[0] != additionnal_nodes.shape[0]:
                additionnal_nodes_outside = set(
                    map(lambda x: x.wkt, additionnal_nodes["geometry"].to_list())
                ).difference(
                    set(
                        map(
                            lambda x: x.wkt,
                            additionnal_nodes_filtered["geometry"].to_list(),
                        )
                    )
                )
                raise AdditionnalNodesOutsideWorkingArea(
                    f"These following points are outside the working area: {', '.join(additionnal_nodes_outside)}"
                )

            additionnal_nodes = additionnal_nodes_filtered.to_dict("records")

        raw_data_restructured = self.__rebuild_network_data(raw_data)
        raw_data_topology_rebuild = NetworkTopology(
            self.logger,
            raw_data_restructured,
            additionnal_nodes,
            self._TOPO_FIELD,
            self._ID_OSM_FIELD,
            mode,
        ).run()

        return raw_data_topology_rebuild

    def __rebuild_network_data(self, raw_data: List[Dict]) -> List[Dict]:
        self.logger.info("Formating data")

        raw_data = filter(
            lambda x: x[self._FEATURE_TYPE_OSM_FIELD] == self._FEATURE_OSM_TYPE,
            raw_data,
        )
        features: list = []
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
    def _get_query_from_mode(mode: str) -> str:
        return network_queries[mode]["query"]
