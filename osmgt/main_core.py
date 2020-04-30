import os

from osmgt.apis.nominatim import NominatimApi
from osmgt.apis.overpass import OverpassApi

import numpy as np
import pickle

import geopandas as gpd

from shapely.geometry import Point
from shapely.geometry import LineString

import geojson

from osmgt.common.osmgt_core import OsmGtCore

# from osmgt.network.graphtools_helper import GraphHelpers

from osmgt.geometry.reprojection import ogr_reproject
from osmgt.geometry.geom_network_cleaner import GeomNetworkCleaner


class OsmGtCoreError(ValueError):
    pass


class MainCore(OsmGtCore):

    __NUMBER_OF_NODES_INTERSECTIONS = 2
    __NEXT_INDEX = 1
    __ITEM_LIST_SEPARATOR = "_"
    __GRAPH_FIELDS = {"node_1", "node_2", "geometry", "length"}
    __ID_FIELD = "uuid"

    __LOCATION_OSM_DEFAULT_ID = 3600000000  # this is it...

    __DEFAULT_OUTPUT_NETWORK_FILE_PATH = "%s_network"

    def __init__(self, **kwargs):
        super().__init__(logger_name="osmgt")

        self.__output = []

    def get_data_from_osm(self, location_name, additionnal_points=None):
        # TODO check variables

        self.logger.info(f"Working location: {location_name}")
        self.__format_output_file_name(location_name.lower())

        location_id = NominatimApi(self.logger, q=location_name, limit=1).data()[0]["osm_id"]
        location_id += self.__LOCATION_OSM_DEFAULT_ID
        raw_data = OverpassApi(self.logger, location_osm_id=location_id).data()["elements"]
        raw_data_restructured = self.__prepare_network_to_be_cleaned(raw_data)
        self.__output = GeomNetworkCleaner(self.logger, raw_data_restructured, additionnal_points).run()

        return self

    def get_data_from_osmgt_file(self, osmgt_input_file_path):
        # TODO check variable

        input_file_name = os.path.splitext(os.path.basename(osmgt_input_file_path))[0]
        self.__format_output_file_name(input_file_name)

        self.__output = self.__open_from_pikle_file(osmgt_input_file_path)

        return self

    def get_gdf(self):
        self.logger.info(f"Prepare Geodataframe")

        features = []
        for feature in self.__output:
            geometry = feature["geometry"]
            properties = {
                key: feature[key] for key in feature.keys()
                if key not in self.__GRAPH_FIELDS
            }
            feature = geojson.Feature(
                geometry=geometry,
                properties=properties
            )
            features.append(feature)

        output = gpd.GeoDataFrame.from_features(features)
        output.crs = self.epsg_4236
        output = output.to_crs(self.epsg_3857)

        return output

    def export_to_geojson(self):
        output_gdf = self.get_gdf()
        output_path = f"{self.__DEFAULT_OUTPUT_NETWORK_FILE_PATH}.geojson"
        self.logger.info(f"Exporting to {output_path}...")
        output_gdf.to_file(output_path, driver="GeoJSON")

    # def to_graph(self):
    #     graph = GraphHelpers()
    #
    #     for feature in self.__output:
    #         graph.add_edge(
    #             str(feature["node_1"]),
    #             str(feature["node_2"]),
    #             feature["id"],
    #             feature["length"],
    #         )
    #     return graph

    def export_to_osmgt_file(self, output_file_name=None):

        output_path = f"{self.__DEFAULT_OUTPUT_NETWORK_FILE_PATH}.osmgt"
        if output_file_name is not None:
            output_path = f"{output_file_name}.osmgt"

        self.logger.info(f"Exporting to {output_path}...")

        with open(output_path, "wb") as output:
            pickle.dump(self.__output, output)

    def __open_from_pikle_file(self, numpy_file_path):
        self.logger.info("Opening from numpy file...")
        with open(numpy_file_path, "rb") as input:
            input_data = pickle.load(input)

        return input_data

    def __prepare_network_to_be_cleaned(self, raw_data):
        self.logger.info("Prepare Data")

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

    def __format_output_file_name(self, title):
        self.__DEFAULT_OUTPUT_NETWORK_FILE_PATH = os.path.join(os.getcwd(), self.__DEFAULT_OUTPUT_NETWORK_FILE_PATH % title)
