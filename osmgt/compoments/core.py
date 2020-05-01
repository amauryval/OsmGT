import os
import sys

import datetime

import logging

import pickle

import geopandas as gpd


class OsmGtCore:
    # LOGGER VARIABLE
    _log_dir = "logs"
    _formatter = logging.Formatter(
        "%(asctime)s - %(name)-15s - %(levelname)-8s : %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    _log_date_file_format = datetime.datetime.now().strftime("%Y_%m_%d_%H%M%S")

    def __init__(
        self,
        parent=None,
        logger_name=None,
        logger_level="info",
        logger_dir=None,
        raise_error=False,
    ):
        if not parent:
            self.__logger_name = logger_name if logger_name else self.__class__.__name__

            self.logger = self.__create_logger(
                logger_level,
                f"/{logger_dir}/{self.__class__.__name__}"
                if logger_dir is not None
                else None,
            )
            self.raise_error = raise_error

        else:
            self.logger_name = parent.logger_name
            self.logger = parent.logger
            self.raise_error = parent.raise_error

    def __create_logger(self, logger_level, logger_dir):
        """
        create a logger

        :param logger_level: str
        :param logger_file: str
        :return:
        """

        levels = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }

        logger_init = logging.getLogger(self.__logger_name)
        logger_init.setLevel(
            levels[logger_level] if logger_level in levels else logging.DEBUG
        )

        if not logger_init.handlers:
            logger_init.setLevel(
                levels[logger_level] if logger_level in levels else logging.DEBUG
            )

            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(
                levels[logger_level] if logger_level in levels else logging.DEBUG
            )
            handler.setFormatter(self._formatter)
            logger_init.addHandler(handler)

            if logger_dir is not None:
                log_path = f"{self._log_dir}_{self._log_date_file_format}"
                complete_log_path = f"{log_path}{os.path.dirname(logger_dir)}"

                if not os.path.isdir(complete_log_path):
                    os.makedirs(complete_log_path)

                handler_file = logging.FileHandler(f"{log_path}{logger_dir}.txt")
                handler_file.setLevel(
                    levels[logger_level] if logger_level in levels else logging.DEBUG
                )
                handler_file.setFormatter(self._formatter)
                logger_init.addHandler(handler_file)

        return logger_init

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

    def convert_list_to_gdf(self, features):
        output_gdf = gpd.GeoDataFrame.from_features(features)
        output_gdf.crs = self.epsg_4236
        output_gdf = output_gdf.to_crs(self.epsg_3857)
        return output_gdf

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