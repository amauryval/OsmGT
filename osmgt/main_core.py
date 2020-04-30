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

    _ways_to_add = []

    def __init__(self, **kwargs):
        super().__init__(logger_name=kwargs.get("logger_name", None))

        location_name = kwargs.get("location_name", None)
        additionnal_points = kwargs.get("additionnal_points", None)
        numpy_file_path = kwargs.get("numpy_file_path", None)

        self._output = []
        self._output_numpy_file_name = f"{location_name}_network"

        self.logger.info(f"========== OSMGT ==========")

        if location_name is not None and numpy_file_path is not None:
            raise OsmGtCoreError(f"Define a location name OR an input numpy file, not both!")

        if location_name is not None:
            self.logger.info(f"Working location: {location_name}")
            # data processing
            self.__get_data_from_osm(location_name)
            raw_data_restructured = self.__prepare_network_to_be_cleaned()
            self._output = GeomNetworkCleaner(self.logger, raw_data_restructured, additionnal_points).run()

        elif numpy_file_path is not None:
            self._output_numpy_file_name = numpy_file_path
            self._output = self._open_from_numpy_file(numpy_file_path)

    def __get_data_from_osm(self, location_name):
        location_id = NominatimApi(self.logger, q=location_name, limit=1).data()[0]["osm_id"]
        location_id += self.__LOCATION_OSM_DEFAULT_ID
        raw_data = OverpassApi(self.logger, location_osm_id=location_id).data()["elements"]
        self._raw_data = filter(lambda x: x["type"] == "way", raw_data)

    def __prepare_network_to_be_cleaned(self):
        self.logger.info("Prepare Data")

        raw_data_reprojected = []
        for feature in self._raw_data:
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

    def to_gdf(self, export_to_file=False):
        self.logger.info(f"Prepare Geodataframe")

        features = []
        for feature in self._output:
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

        return self.__export_to_geofile(output, export_to_file)

    def to_points(self):
        nodes_found = filter(lambda feature: feature["type"] == "node", self._raw_data)

        features = [
            geojson.Feature(
                geometry=Point(feature["lon"], feature["lat"]),
                properties=self._get_tags(feature)
            )
            for feature in nodes_found
        ]
        return self.__export_to_geofile(features)

    # def to_graph(self):
    #     graph = GraphHelpers()
    #
    #     for feature in self._output:
    #         graph.add_edge(
    #             str(feature["node_1"]),
    #             str(feature["node_2"]),
    #             feature["id"],
    #             feature["length"],
    #         )
    #     return graph

    def export_source(self, output_file_name=None):
        self.logger.info("Start: Exporting to numpy file...")

        if output_file_name is not None:
            self._output_numpy_file_name = output_file_name

        with open(f"{self._output_numpy_file_name}.pkl", "wb") as output:
            pickle.dump(self._output, output)

        # np.save(f"{self._output_numpy_file_name}.npy", self._output)
        self.logger.info("END: Exporting to numpy file...")

    def _get_tags(self, feature):
        return feature.get("tags", {})

    def _open_from_numpy_file(self, numpy_file_path):
        self.logger.info("Start: opening from numpy file...")

        # input_data = np.load(numpy_file_path, allow_pickle=True)
        with open(numpy_file_path, "rb") as input:
            input_data = pickle.load(input)
        self.logger.info("Done: opening from numpy file...")

        return input_data

    def __export_to_geofile(self, output, export_to_file):
        if export_to_file:
            output_file = os.path.join(os.getcwd(), f"{self._output_numpy_file_name}.geojson")
            self.logger.info(f"Exporting to {output_file}...")
            output.to_file(output_file, driver="GeoJSON")
        return output
