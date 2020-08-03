import pickle

import geopandas as gpd
import geojson

from osmgt.helpers.logger import Logger

from osmgt.apis.nominatim import NominatimApi


class ErrorOsmGtCore(Exception):
    pass


class OsmGtCore(Logger):
    __NOMINATIM_DEFAULT_ID = 3600000000  # this is it
    __USELESS_COLUMNS = []
    _location_id = None
    TOPO_FIELD = "topo_uuid"

    def __init__(self):
        super().__init__()

    def from_location(self, location_name):
        self.logger.info(f"From location: {location_name}")
        self.logger.info("Loading data...")

        location_found = list(NominatimApi(self.logger, q=location_name, limit=1).data())

        if len(location_found) == 0:
            raise ErrorOsmGtCore("Location not found!")
        elif len(location_found) > 1:
            self.logger.warning(f"Multiple locations found for {location_name} ; the first will be used")
        location_id = location_found[0]["osm_id"]

        self._location_id = self.location_osm_default_id_computing(location_id)

    def from_bbox(self, bbox_value):
        self.logger.info(f"From bbox: {bbox_value}")
        self.logger.info("Loading data...")

    @staticmethod
    def from_location_name_query_builder(location_osm_id, query):
        geo_tag_query = "area.searchArea"
        query = query.format(geo_filter=geo_tag_query)
        return f"area({location_osm_id})->.searchArea;({query});out geom;(._;>;);"

    @staticmethod
    def from_bbox_query_builder(bbox_value, query):
        assert isinstance(bbox_value, tuple)
        assert len(bbox_value) == 4
        bbox_value_formated = ", ".join(map(str, bbox_value))
        query = query.format(geo_filter=bbox_value_formated)
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

    def get_gdf(self, verbose=True):
        if verbose:
            self.logger.info(f"Prepare Geodataframe")

        if not isinstance(self._output_data, gpd.GeoDataFrame):
            self.check_build_input_data()

            output_gdf = gpd.GeoDataFrame.from_features(self._output_data)

        else:
            output_gdf = self._output_data

        output_gdf.crs = self.epsg_4236
        output_gdf = self._clean_attributes(output_gdf)

        return output_gdf

    def check_build_input_data(self):
        if self._output_data is None:
            raise ErrorOsmGtCore("Data is empty!")

    def _clean_attributes(self, input_gdf):
        for col_name in input_gdf.columns:
            if col_name in self.__USELESS_COLUMNS:
                input_gdf.drop(columns=[col_name], inplace=True)

        return input_gdf

    @property
    def epsg_4236(self):
        return "EPSG:4326"

    def location_osm_default_id_computing(self, osm_location_id):
        return osm_location_id + self.__NOMINATIM_DEFAULT_ID

    def _build_feature_from_osm(self, uuid_enum, geometry, properties):

        properties_found = properties.get("tags", {})
        properties_found["id"] = properties["id"]

        # used for topology
        properties_found["bounds"] = ", ".join(map(str, geometry.bounds))
        properties_found[self.TOPO_FIELD] = uuid_enum  # do not cast to str, because topology processing need integer...

        # TODO add CRS
        feature_build = geojson.Feature(geometry=geometry, properties=properties_found)

        return feature_build
