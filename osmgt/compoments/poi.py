import geopandas as gpd
from typing import Tuple
from typing import List
from typing import Optional
from typing import Dict

from osmgt.compoments.core import OsmGtCore

from shapely.geometry import Point

from osmgt.core.global_values import poi_query


class ErrorPoiData(Exception):
    pass


class OsmGtPoi(OsmGtCore):

    _FEATURE_OSM_TYPE: str = "node"

    def __init__(self) -> None:
        super().__init__()

    def from_location(self, location_name: str):
        super().from_location(location_name)

        request = self._from_location_name_query_builder(self._location_id, poi_query)
        raw_data = self._query_on_overpass_api(request)
        self._output_data = self.__build_points(raw_data)

        return self

    def from_bbox(self, bbox_value: Tuple[float, float, float, float]) -> None:
        super().from_bbox(bbox_value)

        request = self._from_bbox_query_builder(self._bbox_value, poi_query)
        raw_data = self._query_on_overpass_api(request)
        self._output_data = self.__build_points(raw_data)


    def __build_points(self, raw_data: List[Dict]) -> List[Dict]:
        self.logger.info("Formating data")

        raw_data = filter(
            lambda x: x[self._FEATURE_TYPE_OSM_FIELD] == self._FEATURE_OSM_TYPE,
            raw_data,
        )
        features = []
        for uuid_enum, feature in enumerate(raw_data, start=1):

            geometry = Point(feature[self._LNG_FIELD], feature[self._LAT_FIELD])
            del feature[self._LNG_FIELD]
            del feature[self._LAT_FIELD]

            feature_build = self._build_feature_from_osm(uuid_enum, geometry, feature)
            features.append(feature_build)

        return features
