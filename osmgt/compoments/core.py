from typing import Tuple
from typing import List
from typing import Optional
from typing import Dict
from typing import Union

import pandas as pd
import geopandas as gpd

from osmgt.helpers.logger import Logger

from osmgt.apis.nominatim import NominatimApi
from osmgt.apis.overpass import OverpassApi

from osmgt.core.global_values import network_queries
from osmgt.core.global_values import epsg_4326
from osmgt.core.global_values import out_geom_query

from shapely.geometry import Point
from shapely.geometry import LineString
from shapely.geometry import Polygon
from shapely.geometry import box


class ErrorOsmGtCore(Exception):
    pass


class IncompatibleFormat(Exception):
    pass


class EmptyData(Exception):
    pass


class OsmGtCore(Logger):

    _QUERY_ELEMENTS_FIELD: str = "elements"
    __USELESS_COLUMNS: List = []
    _location_id: None = None

    _NOMINATIM_DEFAULT_ID: int = 3600000000  # this is it
    _NOMINATIM_OSM_ID_FIELD: str = "osm_id"
    _NOMINATIM_NUMBER_RESULT: str = 1
    _NOMINATIM_GEOJSON_FIELD: str = "geojson"
    _DEFAULT_NAN_VALUE_TO_USE: str = "None"

    _GEOMETRY_FIELD: str = "geometry"
    _LAT_FIELD: str = "lat"
    _LNG_FIELD: str = "lon"

    _TOPO_FIELD: str = "topo_uuid"

    _FEATURE_TYPE_OSM_FIELD: str = "type"
    _PROPERTIES_OSM_FIELD: str = "tags"
    _ID_OSM_FIELD: str = "id"

    def __init__(self) -> None:
        super().__init__()

        self.study_area_geom: None

        self._output_data: Optional[Union[gpd.geodataframe, List[Dict]]]
        self._bbox_value: Optional[Tuple[float, float, float, float]] = None
        self._bbox_mode: bool = False

    def from_location(self, location_name: str) -> None:
        self.logger.info(f"From location: {location_name}")
        self.logger.info("Loading data...")

        location_found = list(
            NominatimApi(
                self.logger, q=location_name, limit=self._NOMINATIM_NUMBER_RESULT
            ).data()
        )

        if len(location_found) == 0:
            raise ErrorOsmGtCore("Location not found!")
        elif len(location_found) > 1:
            self.logger.warning(
                f"Multiple locations found for {location_name} ; the first will be used"
            )
        location_id = location_found[0][self._NOMINATIM_OSM_ID_FIELD]
        self.study_area_geom = Polygon(
            location_found[0][self._NOMINATIM_GEOJSON_FIELD]["coordinates"][0]
        )

        self._location_id = self._location_osm_default_id_computing(location_id)

    def from_bbox(self, bbox_value: Tuple[float, float, float, float]) -> None:
        self._bbox_mode: bool = True
        self.logger.info(f"From bbox: {bbox_value}")
        self.logger.info("Loading data...")
        self.study_area_geom: Polygon = box(*bbox_value, ccw=True)
        # reordered because of nominatim
        self._bbox_value = (bbox_value[1], bbox_value[0], bbox_value[3], bbox_value[2])

    def _get_study_area_from_bbox(self, bbox: Tuple[float, float, float, float]) -> None:
        return

    def _query_on_overpass_api(self, request: str) -> List[Dict]:
        return OverpassApi(self.logger).query(request)[self._QUERY_ELEMENTS_FIELD]

    @staticmethod
    def _from_location_name_query_builder(location_osm_id: int, query: str) -> str:
        geo_tag_query: str = "area.searchArea"
        query = query.format(geo_filter=geo_tag_query)
        return f"area({location_osm_id})->.searchArea;({query});{out_geom_query};"

    def _build_network_from_gdf(self, input_gdf: gpd.GeoDataFrame) -> List[Dict]:
        if isinstance(input_gdf, gpd.GeoDataFrame):
            input_gdf: gpd.GeoDataFrame = self._check_topology_field(input_gdf)
            raw_data: List[Dict] = input_gdf.to_dict("records")

        else:
            raise IncompatibleFormat(
                f"{type(input_gdf)} type not supported. Use a geodataframe."
            )

        return raw_data

    @staticmethod
    def _from_bbox_query_builder(bbox_value: Tuple[float, float, float, float], query: str) -> str:
        assert isinstance(bbox_value, tuple)
        assert len(bbox_value) == 4
        bbox_value_formated = ", ".join(map(str, bbox_value))
        query = query.format(geo_filter=bbox_value_formated)
        return f"({query});{out_geom_query};"

    def _check_topology_field(self, input_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        if self._TOPO_FIELD not in input_gdf.columns.tolist():
            input_gdf[self._TOPO_FIELD] = input_gdf.index.apply(lambda x: int(x))

        input_gdf = input_gdf.fillna(self._DEFAULT_NAN_VALUE_TO_USE)
        return input_gdf

    def get_gdf(self, verbose: bool = True) -> gpd.GeoDataFrame:
        if verbose:
            self.logger.info("Prepare Geodataframe")

        if len(self._output_data) == 0:
            raise EmptyData(
                "Geodataframe creation is impossible, because no data has been found"
            )

        if not isinstance(self._output_data, gpd.GeoDataFrame):
            self._check_build_input_data()
            # more performance comparing .from_features() method
            df: pd.DataFrame = pd.DataFrame(self._output_data)
            geometry = df[self._GEOMETRY_FIELD]  # TODO check type
            output_gdf: gpd.GeoDataFrame = gpd.GeoDataFrame(
                df.drop([self._GEOMETRY_FIELD], axis=1),
                crs=f"EPSG:{epsg_4326}",
                geometry=geometry.to_list(),
            )

        else:
            output_gdf: gpd.GeoDataFrame = self._output_data

        output_gdf: gpd.GeoDataFrame = self._clean_attributes(output_gdf)
        self.logger.info("Geodataframe Ready")

        return output_gdf

    def _check_build_input_data(self) -> None:
        if self._output_data is None:
            raise ErrorOsmGtCore("Data is empty!")

    def _clean_attributes(self, input_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        for col_name in input_gdf.columns:
            if col_name in self.__USELESS_COLUMNS:
                input_gdf.drop(columns=[col_name], inplace=True)

        return input_gdf

    def _location_osm_default_id_computing(self, osm_location_id: int) -> int:
        return osm_location_id + self._NOMINATIM_DEFAULT_ID

    def _build_feature_from_osm(self, uuid_enum: int, geometry: Union[Point, LineString], properties: Dict) -> Dict:
        properties_found: Dict = properties.get(self._PROPERTIES_OSM_FIELD, {})
        properties_found[self._ID_OSM_FIELD] = properties[self._ID_OSM_FIELD]

        # used for topology
        properties_found[
            self._TOPO_FIELD
        ] = uuid_enum  # do not cast to str, because topology processing need an int..
        properties_found[self._GEOMETRY_FIELD] = geometry
        feature_build: Dict = properties_found

        return feature_build

    @staticmethod
    def _check_transport_mode(mode: str) -> None:
        assert (
            mode in network_queries.keys()
        ), f"'{mode}' not found in {', '.join(network_queries.keys())}"
