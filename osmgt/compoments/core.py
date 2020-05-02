import os
import sys

import datetime

import logging

import pickle

import geopandas as gpd

from osmgt.compoments.logger import Logger


class OsmGtCore(Logger):

    def __init__(self):
        super().__init__()

    def from_osmgt_file(self, osmgt_file_path):
        assert ".osmgt" in osmgt_file_path

        self.logger.info(f"Opening from {osmgt_file_path}...")
        with open(osmgt_file_path, "rb") as input_file:
            self._output_data = pickle.load(input_file)

        return self

    def export_to_osmgt_file(self, output_file_name):
        output_path = f"{output_file_name}.osmgt"
        self.logger.info(f"Exporting to {output_path}...")

        with open(output_path, "wb") as output_file:
            pickle.dump(self._output_data, output_file)

    @property
    def epsg_4236(self):
        return 4326

    @property
    def epsg_3857(self):
        return 4326

    @property
    def location_osm_default_id(self):
        return 3600000000  # this is it...

    @property
    def graph_fields(self):
        return {"node_1", "node_2", "geometry", "length"}

    def _convert_list_to_gdf(self, features):
        output_gdf = gpd.GeoDataFrame.from_features(features)
        output_gdf.crs = self.epsg_4236
        output_gdf = output_gdf.to_crs(self.epsg_3857)
        return output_gdf
