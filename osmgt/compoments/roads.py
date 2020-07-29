from osmgt.compoments.core import OsmGtCore

from osmgt.apis.overpass import OverpassApi

from osmgt.geometry.nodes_topology import NodesTopology

from shapely.geometry import LineString
from shapely.geometry import Point
from shapely.wkt import loads
from osmgt.network.gt_helper import GraphHelpers
import geopandas as gpd
from shapely.geometry import shape


class OsmGtRoads(OsmGtCore):

    __DATA_NAME = "network"
    _output_data = None

    def __init__(self):
        super().__init__()

    def from_location(self, location_name, additionnal_nodes=None):
        super().from_location(location_name)

        request = self.from_location_name_query_builder(self._location_id, self.__roads_query)
        raw_data = OverpassApi(self.logger).query(request)["elements"]
        self._output_data = self.__build_network_topology(raw_data, additionnal_nodes)
        #TODO ugly
        self._output_data = self.__post_processing().__geo_interface__["features"]

        return self

    def from_bbox(self, bbox_value, additionnal_nodes=None):
        super().from_bbox(bbox_value)

        request = self.from_bbox_query_builder(bbox_value, self.__roads_query)
        raw_data = OverpassApi(self.logger).query(request)["elements"]
        self._output_data = self.__build_network_topology(raw_data, additionnal_nodes)
        #TODO ugly
        self._output_data = self.__post_processing().__geo_interface__["features"]

        return self

    def __post_processing(self):
        output_gdf = super().get_gdf()

        # build backward and forward roads
        output_gdf.loc[output_gdf['oneway'] == "yes", "direction"] = "forward"
        output_gdf.loc[output_gdf['oneway'] != "yes", "direction"] = "forward;backward"
        output_gdf["geometry"] = output_gdf["geometry"].apply(lambda x: x.wkt)
        output_gdf = (
            output_gdf.set_index(output_gdf.columns.to_list()[:-1])[output_gdf.columns.to_list()[-1]]
            .str.split(';', expand=True)
            .stack()
            .reset_index(level=2, drop=True)
            .reset_index(name='direction')
        )
        output_gdf["topo_uuid"] = output_gdf.apply(lambda x: f"{x['topo_uuid']}_{x['direction']}", axis=1)
        output_gdf["id"] = output_gdf.apply(lambda x: f"{x['id']}_{x['direction']}", axis=1)
        output_gdf["geometry"] = output_gdf.apply(lambda x: loads(x["geometry"]) if x["direction"] == "forward" else LineString(loads(x["geometry"]).coords[::-1]), axis=1)
        output_gdf = gpd.GeoDataFrame(output_gdf, geometry='geometry')
        output_gdf.set_crs(epsg=4326)
        output_gdf.drop(columns=output_gdf.columns.to_list()[-2:], inplace=True)

        return output_gdf

    def get_graph(self):
        self.logger.info("Prepare graph")
        self.check_build_input_data()
        graph = GraphHelpers()

        for feature in self._output_data:
            graph.add_edge(
                Point(feature["geometry"]["coordinates"][0]).wkt,
                Point(feature["geometry"]["coordinates"][-1]).wkt,
                feature["properties"][self.TOPO_FIELD],
                shape(feature["geometry"]).length,

            )
        return graph

    def __build_network_topology(self, raw_data, additionnal_nodes):
        raw_data_restructured = self.__rebuild_network_data(raw_data)
        raw_data_topology_rebuild = NodesTopology(
            self.logger, raw_data_restructured, additionnal_nodes, self.TOPO_FIELD
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

    def __roads_query(self, geo_filter):
        query = f'way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|pedestrian|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link|living_street|service|track|bus_guideway|escape|raceway|road|footway|bridleway|steps|corridor|path)$"]["area"!~"."]({geo_filter});'
        return query
