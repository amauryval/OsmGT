import pickle

import geopandas as gpd
import geojson

from osmgt.helpers.logger import Logger

from osmgt.apis.nominatim import NominatimApi


class ErrorOsnGtCore(Exception):
    pass


class OsmGtCore(Logger):

    _location_id = None

    def __init__(self):
        super().__init__()

    def from_location(self, location_name):
        self.logger.info(f"From location: {location_name}")
        self.logger.info("Loading data...")

        location_id = next(iter(NominatimApi(self.logger, q=location_name, limit=1).data()))[
            "osm_id"
        ]
        self._location_id = self.location_osm_default_id_computing(location_id)

    def from_bbox(self, bbox_value):
        self.logger.info(f"From bbox: {bbox_value}")
        self.logger.info("Loading data...")

    @staticmethod
    def from_location_name_query_builder(location_osm_id, query):
        geo_tag_query = "area.searchArea"
        query = query(geo_tag_query)
        return f"area({location_osm_id})->.searchArea;({query});out geom;(._;>;);"

    @staticmethod
    def from_bbox_query_builder(bbox_value, query):
        assert isinstance(bbox_value, tuple)
        assert len(bbox_value) == 4
        bbox_value_formated = ", ".join(map(str, bbox_value))
        query = query(bbox_value_formated)
        return f"({query});out geom;(._;>;);"

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

    def get_gdf(self):
        self.check_build_input_data()

        self.logger.info(f"Prepare Geodataframe")
        output_gdf = gpd.GeoDataFrame.from_features(self._output_data)
        output_gdf.crs = self.epsg_4236
        # output_gdf = output_gdf.to_crs(self.epsg_3857)

        return output_gdf

    def check_build_input_data(self):
        if self._output_data is None:
            raise ErrorOsnGtCore("Data is empty!")

    @property
    def epsg_4236(self):
        return 4326

    @property
    def epsg_3857(self):
        return 4326

    def location_osm_default_id_computing(self, osm_location_id):
        return osm_location_id + 3600000000  #  this is it...

    def _build_feature_from_osm(self, uuid_enum, geometry, properties):

        properties_found = properties.get("tags", {})
        properties_found["id"] = properties["id"]
        properties_found["uuid"] = uuid_enum
        properties_found["bounds"] = ", ".join(map(str, geometry.bounds))

        feature_build = geojson.Feature(geometry=geometry, properties=properties_found)

        return feature_build
