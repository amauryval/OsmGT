import warnings

import logging

from typing import Optional
from typing import List
from typing import Dict
from typing import Tuple
from typing import Union

from osmgt.compoments.roads import OsmGtRoads

from osmgt.helpers.global_values import epsg_4326
from osmgt.helpers.global_values import epsg_3857
from osmgt.helpers.global_values import km_hour_2_m_sec
from osmgt.helpers.global_values import min_2_sec
from osmgt.helpers.global_values import distance_unit
from osmgt.helpers.global_values import time_unit
from osmgt.helpers.global_values import isochrone_display_mode

import math

import geopandas as gpd

import itertools

try:
    from graph_tool.topology import shortest_distance
except ModuleNotFoundError:
    pass

from shapely.geometry import Point

from osmgt.geometry.geom_helpers import split_multiline_to_lines

from collections import Counter

import concurrent.futures

# to facilitate debugging
try:
    from osmgt.network.gt_helper import GraphHelpers
except ModuleNotFoundError:
    pass

warnings.simplefilter(action="ignore", category=UserWarning)


class IsochroneArgError(Exception):
    pass


class IsochroneGeomError(Exception):
    pass


class IsochroneError(Exception):
    pass


class OsmGtIsochrones(OsmGtRoads):
    logging.getLogger("geopandas.geodataframe").setLevel(logging.CRITICAL)

    __DISTANCE_TOLERANCE: float = 1.3
    __ISOCHRONE_NAME_FIELD: str = "iso_name"
    __ISODISTANCE_NAME_FIELD: str = "iso_distance"
    __DISSOLVE_NAME_FIELD: str = "__dissolve__"
    __TOPO_FIELD_REGEX_CLEANER: str = r"_[0-9]+$"
    __NETWORK_MASK: str = "topo_uuids"
    __DECIMAL_ROUNDED: int = 2

    __CLEANING_NETWORK_BUFFER_VALUE: float = 0.000001
    __CLEANING_NETWORK_CAP_STYLE: int = 3
    __CLEANING_NETWORK_RESOLUTION: int = 4
    __ROADS_BUFFER_EROSION_DIVISOR: int = 10

    __DEFAULT_CAPSTYLE: int = 1
    __DEFAULT_JOINSTYLE: int = 1

    __DEFAULT_BUFFER_VALUE_2: float = 0.00001

    __DISTANCE_UNIT_FIELD: str = "distance_unit"
    __TIME_UNIT_FIELD: str = "time_unit"

    def __init__(
            self,
            trip_speed: float,
            isochrones_times: Optional[List],
            distance_to_compute: Optional[List] = None,
    ) -> None:
        super().__init__()
        self.logger.info("Isochrone processing...")

        self.__topo_uuids: List[str] = []
        self._source_node: Optional[str] = None
        self._isochrones_data: List[Dict] = []
        self._source_vertex: Optional[str] = None
        self._location_point_reprojected_buffered_bounds: Optional[Tuple[float]] = None
        self._network_gdf: Optional[gpd.GeoDataFrame] = None
        self._graph: Optional[GraphHelpers] = None

        self._display_mode_params = isochrone_display_mode

        # trip_speed in km/h
        self._speed_to_m_s: float = trip_speed / km_hour_2_m_sec

        if isochrones_times is None and distance_to_compute is None:
            raise IsochroneArgError(
                "class needs one of 'isochrones_times' and 'distance_to_compute'"
            )
        elif isochrones_times is not None and distance_to_compute is not None:
            raise IsochroneArgError(
                "class needs one of 'isochrones_times' and 'distance_to_compute'"
            )

        if isochrones_times is not None:
            self._isochrones_times = self._prepare_isochrone_values_from_times(
                isochrones_times
            )
        elif distance_to_compute is not None:
            self._isochrones_times = self._prepare_isochrone_values_from_distance(
                distance_to_compute
            )

    def _prepare_isochrone_values_from_times(self, isochrones_times: List) -> List:
        isochrones_times.sort()

        # iso time = min
        times_dist: Dict = {
            round(iso_time, self.__DECIMAL_ROUNDED): round(
                math.ceil((iso_time * min_2_sec) * self._speed_to_m_s),
                self.__DECIMAL_ROUNDED,
            )  # distance
            for iso_time in isochrones_times
        }
        self._time_dist = times_dist
        return self._compute_isochrones_ingredient(times_dist)

    def _prepare_isochrone_values_from_distance(
            self, distance_to_compute: List
    ) -> List:
        distance_to_compute.sort()

        times_dist: Dict = {
            round(
                distance / self._speed_to_m_s / min_2_sec, self.__DECIMAL_ROUNDED
            ): round(
                distance, self.__DECIMAL_ROUNDED
            )  # distance
            for distance in distance_to_compute
        }
        self._time_dist = times_dist
        return self._compute_isochrones_ingredient(times_dist)

    @staticmethod
    def _compute_isochrones_ingredient(input_ingredients: Dict) -> List:

        times_dist: List = sorted(
            input_ingredients.items(), key=lambda x: x[1], reverse=True
        )
        return times_dist

    def from_locations_based_on_area_name(self, points_gdf: gpd.GeoDataFrame, area_name: str, mode: str):

        # todo filter points
        # get network and connect pois expected
        self.from_location(area_name, points_gdf, mode, interpolate_lines=True)
        self._final_network_gdf = super().get_gdf()
        # default value
        self._final_network_gdf.loc[":", self.__ISOCHRONE_NAME_FIELD] = 9999
        self._final_network_gdf.loc[":", self.__ISODISTANCE_NAME_FIELD] = 9999

        self._graph = self.get_graph()

        output_data = []
        for _, feature in points_gdf.iterrows():
            isochrones_lines = self.from_location_point(feature.geometry, mode)
            output_data.append(isochrones_lines)

        sorted_dict = sorted(self._time_dist.items(), key=lambda x: x[0], reverse=True)
        for time, dist in sorted_dict:
            topo_uuids = list(itertools.chain(*[
                gdf_data.loc[gdf_data[self.__ISODISTANCE_NAME_FIELD] == dist]["topo_uuid"].tolist()
                for gdf_data in output_data
            ]))
            self._final_network_gdf.loc[
                self._final_network_gdf["topo_uuid"].isin(topo_uuids), self.__ISOCHRONE_NAME_FIELD
            ] = time
            self._final_network_gdf.loc[
                self._final_network_gdf["topo_uuid"].isin(topo_uuids), self.__ISODISTANCE_NAME_FIELD
            ] = dist

        print("a", len(self._final_network_gdf))
        network_gdf = self._finalize_network(self._final_network_gdf)
        print("b", len(network_gdf))

        return network_gdf

    def from_location_point(
            self, location_point: Point, mode: str
    ) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:

        self._network_gdf = self._final_network_gdf.copy()
        self._mode = mode
        self._source_node = location_point.wkt
        self._source_vertex = self._graph.find_vertex_from_name(self._source_node)

        # reset output else isochrone will be append
        self._isochrones_data: List[Dict] = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(self._compute_isochrone, self._isochrones_times)
        # for param in self._isochrones_times:
        #     self._compute_isochrone(param)

        network_gdf = self.__clean_network(self._network_gdf)

        return network_gdf

    def __clean_network(self, network_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        # reverse order for isochrone, because isochrone mask is like russian dolls
        self._isochrones_data = sorted(
            self._isochrones_data,
            key=lambda k: k[self.__ISOCHRONE_NAME_FIELD],
            reverse=True,
        )
        for isochrone_computed in self._isochrones_data:
            if self.__NETWORK_MASK in isochrone_computed:
                network_gdf.loc[
                    isochrone_computed[self.__NETWORK_MASK], self.__ISOCHRONE_NAME_FIELD
                ] = isochrone_computed[self.__ISOCHRONE_NAME_FIELD]
                network_gdf.loc[
                    isochrone_computed[self.__NETWORK_MASK], self.__ISODISTANCE_NAME_FIELD
                ] = isochrone_computed[self.__ISODISTANCE_NAME_FIELD]
                del isochrone_computed[self.__NETWORK_MASK]

        return network_gdf

    def _finalize_network(self, network_gdf):
        network_gdf[self._TOPO_FIELD].replace(
            self.__TOPO_FIELD_REGEX_CLEANER, "", regex=True, inplace=True
        )
        network_gdf[self.__DISSOLVE_NAME_FIELD] = (
                network_gdf[self._TOPO_FIELD].astype(str)
                + "__"
                + network_gdf[self.__ISOCHRONE_NAME_FIELD].astype(str)
        )

        network_gdf = network_gdf.dissolve(
            by=self.__DISSOLVE_NAME_FIELD
        ).reset_index(drop=True)
        # convert multilinestring to LineStrings
        network_gdf = split_multiline_to_lines(
            network_gdf, epsg_4326, self._TOPO_FIELD
        )
        return network_gdf

    def _compute_isochrone(self, params) -> None:

        iso_time, dist = params
        self.logger.info(f"Compute isochrone: {iso_time} minutes => {dist} meters")

        _, pred = shortest_distance(
            self._graph,
            source=self._source_vertex,
            weights=self._graph.edge_weights,
            max_dist=dist,
            return_reached=True,
        )
        points = [self._graph.vertex_names[vertex] for vertex in pred]


        all_edges_found_topo_uuids_count = Counter(
            list(
                itertools.chain(
                    *[self._graph.find_edges_from_vertex(pt) for pt in points]
                )
            )
        )
        all_edges_found_topo_uuids = set(
            list(
                dict(
                    filter(
                        lambda x: x[1] > 1, all_edges_found_topo_uuids_count.items(),
                    )
                ).keys()
            )
        )

        network_mask = self._network_gdf["topo_uuid"].isin(all_edges_found_topo_uuids)
        self._isochrones_data.append(
            {
                self.__ISOCHRONE_NAME_FIELD: iso_time,
                self.__TIME_UNIT_FIELD: time_unit,
                self.__ISODISTANCE_NAME_FIELD: dist,
                self.__DISTANCE_UNIT_FIELD: distance_unit,
                self.__NETWORK_MASK: network_mask,
            }
        )
