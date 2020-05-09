from osmgt.compoments.core import OsmGtCore

from osmgt.apis.overpass import OverpassApi

from osmgt.geometry.reprojection import ogr_reproject

from shapely.geometry import Point


class ErrorPoiData(Exception):
    pass


class OsmGtPoi(OsmGtCore):

    __DATA_NAME = "network"
    _output_data = None

    def __init__(self):
        super().__init__()

    def from_location(self, location_name):
        super().from_location(location_name)

        request = self.from_location_name_query_builder(self._location_id, self.__shop_query)
        raw_data = OverpassApi(self.logger).query(request)["elements"]
        self._output_data = self.__build_points(raw_data)

        return self

    def from_bbox(self, bbox_value):
        super().from_bbox(bbox_value)

        request = self.from_bbox_query_builder(bbox_value, self.__shop_query)
        raw_data = OverpassApi(self.logger).query(request)["elements"]
        self._output_data = self.__build_points(raw_data)

        return self

    def __build_points(self, raw_data):
        self.logger.info("Formating data")

        raw_data = filter(lambda x: x["type"] == "node", raw_data)
        features = []
        for uuid_enum, feature in enumerate(raw_data, start=1):

            geometry = Point(feature["lon"], feature["lat"])
            del feature["lon"]
            del feature["lat"]

            feature_build = self._build_feature_from_osm(uuid_enum, geometry, feature)
            features.append(feature_build)

        return features

    def __shop_query(self, geo_filter):
        return f'node["amenity"]({geo_filter});node[shop]({geo_filter});'
