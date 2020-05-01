import os

from osmgt.compoments.core import OsmGtCore

from osmgt.apis.nominatim import NominatimApi
from osmgt.apis.overpass import OverpassApi

from osmgt.geometry.reprojection import ogr_reproject
from osmgt.geometry.geom_network_cleaner import GeomNetworkCleaner

import geojson
from shapely.geometry import LineString

# from osmgt.network.gt_helper import GraphHelpers


class ErrorNetworkData(Exception):
    pass


class OsmGtNetwork(OsmGtCore):

    __DATA_NAME = "network"
    _output_data = None

    def __init__(self):
        super().__init__()

    def from_location(self, location_name, additionnal_nodes):
        self.logger.info(f"From location: {location_name}")
        self.logger.info("Loading network data...")

        location_id = NominatimApi(self.logger, q=location_name, limit=1).data()[0]["osm_id"]
        location_id += self.location_osm_default_id
        location_id_query_part = self.__from_location_builder(location_id)

        query = f"{location_id_query_part}{self.__road_query}"
        raw_data = OverpassApi(self.logger).querier(query)["elements"]

        self._output_data = self.__build_network_topology(raw_data, additionnal_nodes)

        return self

    def get_gdf(self):
        if self._output_data is None:
            raise ErrorNetworkData("Data is empty!")

        self.logger.info(f"Prepare Geodataframe")

        features = []
        for feature in self._output_data:
            geometry = feature["geometry"]
            properties = {
                key: feature[key] for key in feature.keys()
                if key not in self.graph_fields
            }
            feature = geojson.Feature(
                geometry=geometry,
                properties=properties
            )
            features.append(feature)

        output_gdf = super().convert_list_to_gdf(features)

        return output_gdf

    # def get_graph(self):
    #     if self._output_data is None:
            # raise ErrorNetworkData("Data is empty!")
    #     graph = GraphHelpers()
    #
    #     for feature in self._output_data:
    #         graph.add_edge(
    #             str(feature["node_1"]),
    #             str(feature["node_2"]),
    #             feature["id"],
    #             feature["length"],
    #         )
    #     return graph

    def __build_network_topology(self, raw_data, additionnal_nodes):
        raw_data_restructured = self.__rebuild_network_data(raw_data)
        raw_data_topology_rebuild = GeomNetworkCleaner(
            self.logger,
            raw_data_restructured,
            additionnal_nodes
        ).run()

        return raw_data_topology_rebuild

    def __rebuild_network_data(self, raw_data):
        self.logger.info("Formating data")

        raw_data = filter(lambda x: x["type"] == "way", raw_data)
        raw_data_reprojected = []
        for feature in raw_data:
            try:
                feature["geometry"] = ogr_reproject(
                    LineString([(coords["lon"], coords["lat"]) for coords in feature["geometry"]]),
                    self.epsg_4236, self.epsg_3857
                )
            except:
                feature["geometry"] = LineString([(coords["lon"], coords["lat"]) for coords in feature["geometry"]])

            feature["bounds"] = feature["geometry"].bounds
            feature["geometry"] = feature["geometry"].coords[:]

            raw_data_reprojected.append(feature)

        return raw_data_reprojected

    @property
    def __road_query(self):
        return '(way["highway"](area.searchArea););out geom;(._;>;);'

    def __from_location_builder(self, location_osm_id):
        return f"area({location_osm_id})->.searchArea;"
