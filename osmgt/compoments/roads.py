from osmgt.compoments.core import OsmGtCore

from osmgt.apis.overpass import OverpassApi

from osmgt.geometry.network_topology import NetworkTopology

from shapely.geometry import LineString
from shapely.geometry import Point
from shapely.wkt import loads
# from osmgt.network.gt_helper import GraphHelpers
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
        self._output_data = self.__build_network_topology(raw_data, additionnal_nodes)

        return self

    def from_bbox(self, bbox_value, additionnal_nodes=None, mode="vehicle"):
        super().from_bbox(bbox_value)
        self._mode = mode

        query = self.get_query_from_mode(mode)
        request = self.from_bbox_query_builder(bbox_value, query)
        raw_data = OverpassApi(self.logger).query(request)["elements"]
        self._output_data = self.__build_network_topology(raw_data, additionnal_nodes)

        return self

    def __DEPRECATED_direction_processing(self):
        output_gdf = super().get_gdf(verbose=False)

        # build backward and forward roads
        # by default
        output_gdf.loc[:, "direction"] = "forward;backward"
        if "oneway" in output_gdf.columns.to_list():
            output_gdf.loc[output_gdf['oneway'] == "yes", "direction"] = "forward"
            output_gdf.loc[output_gdf['oneway'] != "yes", "direction"] = "forward;backward"

        if "junction" in output_gdf.columns.to_list():
            output_gdf.loc[output_gdf['junction'].isin(["roundabout", "jughandle"]), "direction"] = "forward"

        output_gdf["geometry"] = output_gdf["geometry"].apply(lambda x: x.wkt)

        output_gdf = (
            output_gdf.set_index(output_gdf.columns.to_list()[:-1])[output_gdf.columns.to_list()[-1]]
            .str.split(';', expand=True)
            .stack()
            .reset_index(name='direction')
        )
        underscore_concat = lambda a, b: f"{a}_{b}"
        output_gdf["topo_uuid"] = output_gdf["topo_uuid"].combine(output_gdf["direction"], underscore_concat)
        output_gdf["id"] = output_gdf["id"].combine(output_gdf["direction"], underscore_concat)

        output_gdf["geometry"] = output_gdf.apply(lambda x: loads(x["geometry"]) if x["direction"] == "forward" else LineString(loads(x["geometry"]).coords[::-1]), axis=1)
        output_gdf = gpd.GeoDataFrame(output_gdf, geometry='geometry')
        output_gdf.set_crs(epsg=4326)
        output_gdf.drop(columns=output_gdf.columns.to_list()[-2:], inplace=True)

        return output_gdf

    # def get_graph(self):
    #     self.logger.info("Prepare graph")
    #     self.check_build_input_data()
    #
    #     if self._mode == "vehicle":
    #         graph = GraphHelpers(is_directed=True)
    #     elif self._mode == "pedestrian":
    #         graph = GraphHelpers(is_directed=False)
    #
    #     for feature in self._output_data:
    #         graph.add_edge(
    #             Point(feature["geometry"].coords[0]).wkt,
    #             Point(feature["geometry"].coords[-1]).wkt,
    #             feature["properties"][self.TOPO_FIELD],
    #             shape(feature["geometry"]).length,
    #         )
    #     return graph

    def __build_network_topology(self, raw_data, additionnal_nodes):
        raw_data_restructured = self.__rebuild_network_data(raw_data)
        raw_data_topology_rebuild = NetworkTopology(
            self.logger, raw_data_restructured, additionnal_nodes, self.TOPO_FIELD, self._mode
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
        assert mode in network_queries.keys()
        return network_queries[mode]
        # if mode == "car":
        #     query = self.__vehicule_path_query()
        # elif mode == "pedestrian":
        #     query = self.__pedestrian_path_query()
        #
        # return query

    # def __vehicule_path_query(self, geo_filter):
    #     query = f'way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link|living_street|service|track|bus_guideway|escape|raceway|road|footway|bridleway|steps|corridor|path)$"]["area"!~"."]({geo_filter});'
    #     return query
    #
    # def __pedestrian_path_query(self, geo_filter):
    #     query = f'way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|pedestrian|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link|living_street|service|track|bus_guideway|escape|raceway|road|footway|bridleway|steps|corridor|path)$"]["area"!~"."]({geo_filter});'
    #     return query