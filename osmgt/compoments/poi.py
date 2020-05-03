import os

from osmgt.compoments.core import OsmGtCore

from osmgt.apis.nominatim import NominatimApi
from osmgt.apis.overpass import OverpassApi

from osmgt.geometry.reprojection import ogr_reproject

import geojson
from shapely.geometry import Point


class ErrorPoiData(Exception):
    pass


class OsmGtPoi(OsmGtCore):

    __DATA_NAME = "network"
    _output_data = None

    def __init__(self):
        super().__init__()

    def from_location(self, location_name):
        self.logger.info(f"From location: {location_name}")
        self.logger.info("Loading network data...")

        location_id = NominatimApi(self.logger, q=location_name, limit=1).data()[0]["osm_id"]
        location_id += self.location_osm_default_id
        location_id_query_part = self.__from_location_builder(location_id)

        query = f"{location_id_query_part}{self.__shop_query}"
        raw_data = OverpassApi(self.logger).querier(query)["elements"]

        self._output_data = self.__build_points(raw_data)

        return self

    def get_gdf(self, warning_edition=True):
        self.check_build_input_data()

        self.logger.info(f"Prepare Geodataframe")
        if warning_edition:
            self.logger.warning(f"If you modify the geometry output gdf, it will be not compatible with the graph")

        output_gdf = super()._convert_list_to_gdf(self._output_data)

        return output_gdf

    def __build_points(self, raw_data):
        self.logger.info("Formating data")

        raw_data = filter(lambda x: x["type"] == "node", raw_data)
        features = []
        for uuid_enum, feature in enumerate(raw_data, start=1):

            try:
                geometry = ogr_reproject(
                    Point(feature["lon"], feature["lat"]),
                    self.epsg_4236, self.epsg_3857
                )
            except:
                geometry = Point(feature["lon"], feature["lat"])
            del feature["lon"]
            del feature["lat"]

            properties = feature
            del feature["type"]
            properties["bounds"] = ", ".join(map(str, geometry.bounds))
            properties["uuid"] = uuid_enum
            properties = {**properties, **self.insert_tags_field(properties)}
            del feature["tags"]

            feature = geojson.Feature(
                geometry=geometry,
                properties=properties
            )

            features.append(feature)

        return features

    def check_build_input_data(self):
        if self._output_data is None:
            raise ErrorPoiData("Data is empty!")

    @property
    def __shop_query(self):
        return '(node["amenity"](area.searchArea);node[shop](area.searchArea););out geom;(._;>;);'

    def __from_location_builder(self, location_osm_id):
        return f"area({location_osm_id})->.searchArea;"
