import pandas as pd
import geopandas as gpd

from osmgt.helpers.logger import Logger

from osmgt.apis.nominatim import NominatimApi
from osmgt.apis.overpass import OverpassApi

from osmgt.core.global_values import network_queries
from osmgt.core.global_values import epsg_4326
from osmgt.core.global_values import out_geom_query

from shapely.geometry import Polygon
from shapely.geometry import box


class ErrorOsmGtCore(Exception):
    pass


class IncompatibleFormat(Exception):
    pass


class EmptyData(Exception):
    pass



class OsmGtCore(Logger):

    _QUERY_ELEMENTS_FIELD = "elements"
    __USELESS_COLUMNS = []
    _location_id = None

    _NOMINATIM_DEFAULT_ID = 3600000000  # this is it
    _NOMINATIM_OSM_ID_FIELD = "osm_id"
    _NOMINATIM_NUMBER_RESULT = 1
    _NOMINATIM_GEOJSON_FIELD = "geojson"
    _DEFAULT_NAN_VALUE_TO_USE = "None"

    _GEOMETRY_FIELD = "geometry"
    _LAT_FIELD = "lat"
    _LNG_FIELD = "lon"

    _TOPO_FIELD = "topo_uuid"

    _FEATURE_TYPE_OSM_FIELD = "type"
    _PROPERTIES_OSM_FIELD = "tags"
    _ID_OSM_FIELD = "id"

    def __init__(self):
        super().__init__()

        self.study_area_geom = None

        self._output_data = None
        self._bbox_value = None
        self._bbox_mode = False

    def from_location(self, location_name):
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

    def from_bbox(self, bbox_value):
        self._bbox_mode = True
        self.logger.info(f"From bbox: {bbox_value}")
        self.logger.info("Loading data...")
        self.study_area_geom = box(*bbox_value, ccw=True)
        # reordered because of nominatim
        self._bbox_value = (bbox_value[1], bbox_value[0], bbox_value[3], bbox_value[2])

    def from_location_point(self, location_point, isochrones_to_build, mode):
        pass

    def _get_study_area_from_bbox(self, bbox):
        return

    def _query_on_overpass_api(self, request):
        return OverpassApi(self.logger).query(request)[self._QUERY_ELEMENTS_FIELD]

    @staticmethod
    def _from_location_name_query_builder(location_osm_id, query):
        geo_tag_query = "area.searchArea"
        query = query.format(geo_filter=geo_tag_query)
        return f"area({location_osm_id})->.searchArea;({query});{out_geom_query};"

    def _build_network_from_gdf(self, input_gdf):
        if isinstance(input_gdf, gpd.GeoDataFrame):
            input_gdf = self._check_topology_field(input_gdf)
            raw_data = input_gdf.to_dict("records")

        else:
            raise IncompatibleFormat(
                f"{type(input_gdf)} type not supported. Use a geodataframe."
            )

        return raw_data

    @staticmethod
    def _from_bbox_query_builder(bbox_value, query):
        assert isinstance(bbox_value, tuple)
        assert len(bbox_value) == 4
        bbox_value_formated = ", ".join(map(str, bbox_value))
        query = query.format(geo_filter=bbox_value_formated)
        return f"({query});{out_geom_query};"

    def _check_topology_field(self, input_gdf):
        if self._TOPO_FIELD not in input_gdf.columns.tolist():
            input_gdf[self._TOPO_FIELD] = input_gdf.index.apply(lambda x: int(x))

        input_gdf = input_gdf.fillna(self._DEFAULT_NAN_VALUE_TO_USE)
        return input_gdf

    def get_gdf(self, verbose=True):
        if verbose:
            self.logger.info(f"Prepare Geodataframe")

        if len(self._output_data) == 0:
            raise EmptyData("Geodataframe creation is impossible, because no data has been found")

        if not isinstance(self._output_data, gpd.GeoDataFrame):
            self._check_build_input_data()
            # more performance comparing .from_features() method
            df = pd.DataFrame(self._output_data)
            geometry = df[self._GEOMETRY_FIELD]
            output_gdf = gpd.GeoDataFrame(
                df.drop([self._GEOMETRY_FIELD], axis=1),
                crs=f"EPSG:{epsg_4326}",
                geometry=geometry.to_list(),
            )

        else:
            output_gdf = self._output_data

        output_gdf = self._clean_attributes(output_gdf)
        self.logger.info(f"Geodataframe Ready")

        return output_gdf

    def _check_build_input_data(self):
        if self._output_data is None:
            raise ErrorOsmGtCore("Data is empty!")

    def _clean_attributes(self, input_gdf):
        for col_name in input_gdf.columns:
            if col_name in self.__USELESS_COLUMNS:
                input_gdf.drop(columns=[col_name], inplace=True)

        return input_gdf

    def _location_osm_default_id_computing(self, osm_location_id):
        return osm_location_id + self._NOMINATIM_DEFAULT_ID

    def _build_feature_from_osm(self, uuid_enum, geometry, properties):
        properties_found = properties.get(self._PROPERTIES_OSM_FIELD, {})
        properties_found[self._ID_OSM_FIELD] = properties[self._ID_OSM_FIELD]

        # used for topology
        properties_found[
            self._TOPO_FIELD
        ] = uuid_enum  # do not cast to str, because topology processing need an int..
        properties_found[self._GEOMETRY_FIELD] = geometry
        feature_build = properties_found

        return feature_build

    @staticmethod
    def _check_transport_mode(mode):
        assert (
            mode in network_queries.keys()
        ), f"'{mode}' not found in {', '.join(network_queries.keys())}"
