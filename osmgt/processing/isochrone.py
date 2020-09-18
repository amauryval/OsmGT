import warnings

import logging

from typing import Optional
from typing import List
from typing import Dict
from typing import Tuple

from osmgt.compoments.roads import OsmGtRoads

from osmgt.helpers.global_values import epsg_4326
from osmgt.helpers.global_values import epsg_3857
from osmgt.helpers.global_values import km_hour_2_m_sec
from osmgt.helpers.global_values import min_2_sec
from osmgt.helpers.global_values import distance_unit
from osmgt.helpers.global_values import time_unit
from osmgt.helpers.global_values import isochrone_display_mode
from osmgt.helpers.global_values import water_area_query

from osmgt.helpers.misc import find_index

import math

from operator import itemgetter

import geopandas as gpd
import pandas as pd

import itertools

try:
    from graph_tool.topology import shortest_distance
except ModuleNotFoundError:
    pass

from shapely.geometry import base
from shapely.geometry import Point
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon

from osmgt.geometry.geom_helpers import reprojection
from osmgt.geometry.geom_helpers import split_multiline_to_lines
from osmgt.geometry.geom_helpers import convert_to_polygon

from shapely.ops import unary_union

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


class OsmGtIsochrone(OsmGtRoads):
    logging.getLogger("geopandas.geodataframe").setLevel(logging.CRITICAL)

    __DISTANCE_TOLERANCE: float = 1.3
    __ISOCHRONE_NAME_FIELD: str = "iso_name"
    __ISODISTANCE_NAME_FIELD: str = "iso_distance"
    __DISSOLVE_NAME_FIELD: str = "__dissolve__"
    __TOPO_FIELD_REGEX_CLEANER = r"_[0-9]+$"
    __TOPO_UIIDS_FIELD = "topo_uuids"

    __CLEANING_NETWORK_BUFFER_VALUE: float = 0.000001
    __CLEANING_NETWORK_CAP_STYLE: int = 3
    __CLEANING_NETWORK_RESOLUTION: int = 4

    __DEFAULT_ISOCHRONE_CAPSTYLE = 1
    __DEFAULT_ISOCHRONE_JOINSTYLE = 1

    __DEFAULT_BUFFER_VALUE_2: float = 0.00001

    __DISTANCE_UNIT_FIELD = "distance_unit"
    __TIME_UNIT_FIELD = "time_unit"

    def __init__(
            self,
            trip_speed: float,
            isochrones_times: Optional[List],
            distance_to_compute: Optional[List] = None,
    ) -> None:
        super().__init__()
        self.logger.info("Isochrone processing...")

        self.__topo_uuids: List[str] = []
        self.source_node: Optional[str] = None
        self._isochrones_data: List[Dict] = []

        self._display_mode_params = isochrone_display_mode

        # trip_speed in km/h
        self._speed_to_m_s: float = trip_speed / km_hour_2_m_sec

        isochrones_times = isochrones_times
        distance_to_compute = distance_to_compute

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
            round(iso_time, 2): round(
                math.ceil((iso_time * min_2_sec) * self._speed_to_m_s), 2
            )  # distance
            for iso_time in isochrones_times
        }
        return self._compute_isochrones_ingredient(times_dist)

    def _prepare_isochrone_values_from_distance(
            self, distance_to_compute: List
    ) -> List:
        distance_to_compute.sort()

        times_dist: Dict = {
            round(distance / self._speed_to_m_s / min_2_sec, 2): round(
                distance, 2
            )  # distance
            for distance in distance_to_compute
        }
        return self._compute_isochrones_ingredient(times_dist)

    @staticmethod
    def _compute_isochrones_ingredient(input_ingredients: Dict) -> List:

        times_dist: List = sorted(
            input_ingredients.items(), key=lambda x: x[1], reverse=True
        )
        return times_dist

    def from_location_point(
            self, location_point: Point, mode: str
    ) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:

        self._mode = mode

        self.source_node = location_point.wkt
        # compute bbox
        max_distance = max(self._isochrones_times, key=itemgetter(1))[-1]
        location_point_reproj = reprojection(location_point, epsg_4326, epsg_3857)
        location_point_reproj_buffered = location_point_reproj.buffer(
            max_distance * self.__DISTANCE_TOLERANCE
        )
        self._location_point_reprojected_buffered_bounds = reprojection(
            location_point_reproj_buffered, epsg_3857, epsg_4326
        ).bounds

        additional_nodes = [{self._TOPO_FIELD: 0, "geometry": location_point}]
        df = pd.DataFrame(additional_nodes)
        geometry = df["geometry"]
        additional_nodes_gdf = gpd.GeoDataFrame(
            df.drop(["geometry"], axis=1),
            crs=int(epsg_4326),
            geometry=geometry.to_list(),
        )
        self.from_bbox(
            self._location_point_reprojected_buffered_bounds,
            additional_nodes=additional_nodes_gdf,
            mode=mode,
            interpolate_lines=True,
        )

        # get water area
        bbox_value = (
            self._location_point_reprojected_buffered_bounds[1], self._location_point_reprojected_buffered_bounds[0],
            self._location_point_reprojected_buffered_bounds[3], self._location_point_reprojected_buffered_bounds[2])
        request = self._from_bbox_query_builder(bbox_value, water_area_query)
        raw_data = self._query_on_overpass_api(request)
        water_area = []
        for feature in raw_data:
            if feature["type"] == "relation":
                for member in feature["members"]:
                    water_area.append(Polygon([(geom["lon"], geom["lat"]) for geom in member["geometry"]]))
            else:
                if "geometry" in feature:
                    water_area.append(Polygon([(geom["lon"], geom["lat"]) for geom in feature["geometry"]]))
        self._water_area = unary_union(water_area)

        self._network_gdf = super().get_gdf()
        self._graph = self.get_graph()
        self._source_vertex = self._graph.find_vertex_from_name(self.source_node)
        # reset output else isochrone will be append
        self._output_data = []
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(self._compute_isochrone, self._isochrones_times)
        #         for param in self._isochrones_times:
        #             self._compute_isochrone(param)

        self.__clean_network()
        self.__clean_isochrones()

        self._OUTPUT_EXPECTED_GEOM_TYPE = "Polygon"  # mandatory
        isochrones_gdf = self.get_gdf(verbose=False)

        return isochrones_gdf, self._network_gdf

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

        all_edges_found_topo_uuids = set(
            list(
                itertools.chain(
                    *[self._graph.find_edges_from_vertex(pt) for pt in points]
                )
            )
        )
        network_mask = self._network_gdf["topo_uuid"].isin(all_edges_found_topo_uuids)

        iso_polygon = Polygon(
            self._network_gdf.loc[network_mask]
                .buffer(
                self._display_mode_params["path_buffered"],
                cap_style=self.__DEFAULT_ISOCHRONE_CAPSTYLE,
                join_style=self.__DEFAULT_ISOCHRONE_JOINSTYLE,
                resolution=self._display_mode_params["resolution"],
            )
                .unary_union.buffer(  # merge them now
                self._display_mode_params["dilatation"],
                cap_style=self._display_mode_params["cap_style"],
                join_style=self._display_mode_params["join_style"],
                resolution=self._display_mode_params["resolution"],
            )
                .buffer(
                self._display_mode_params["erosion"],
                cap_style=self._display_mode_params["cap_style"],
                join_style=self._display_mode_params["join_style"],
                resolution=self._display_mode_params["resolution"],
            )
                .exterior
        )
        self._isochrones_data.append(
            {
                self.__ISOCHRONE_NAME_FIELD: iso_time,
                self.__TIME_UNIT_FIELD: time_unit,
                self.__ISODISTANCE_NAME_FIELD: dist,
                self.__DISTANCE_UNIT_FIELD: distance_unit,
                self.__TOPO_UIIDS_FIELD: network_mask,
                "geometry": iso_polygon,
            }
        )

    def __clean_network(self) -> None:
        # reverse order for isochrone, because isochrone mask is like russian dolls
        self._isochrones_data = sorted(
            self._isochrones_data,
            key=lambda k: k[self.__ISOCHRONE_NAME_FIELD],
            reverse=True
        )
        for isochrone_computed in self._isochrones_data:
            self._network_gdf.loc[
                isochrone_computed[self.__TOPO_UIIDS_FIELD], self.__ISOCHRONE_NAME_FIELD
            ] = isochrone_computed[self.__ISOCHRONE_NAME_FIELD]
            self._network_gdf.loc[
                isochrone_computed[self.__TOPO_UIIDS_FIELD], self.__ISODISTANCE_NAME_FIELD
            ] = isochrone_computed[self.__ISODISTANCE_NAME_FIELD]
            del isochrone_computed[self.__TOPO_UIIDS_FIELD]

        self._network_gdf[self._TOPO_FIELD].replace(
            self.__TOPO_FIELD_REGEX_CLEANER, "", regex=True, inplace=True
        )

        self._network_gdf[self.__DISSOLVE_NAME_FIELD] = (
                self._network_gdf[self._TOPO_FIELD].astype(str)
                + "__"
                + self._network_gdf[self.__ISOCHRONE_NAME_FIELD].astype(str)
        )
        self._network_gdf = self._network_gdf.dissolve(
            by=self.__DISSOLVE_NAME_FIELD
        ).reset_index(drop=True)

        # convert multilinestring to LineStrings
        self._network_gdf = split_multiline_to_lines(
            self._network_gdf, epsg_4326, self._TOPO_FIELD
        )

        self._network_gdf = self._network_gdf[
            self._network_gdf[self.__ISOCHRONE_NAME_FIELD].notnull()
        ]

    def __clean_isochrones(self) -> None:
        # find iso index pair in order to create hole geom. isochrones are like russian dolls
        iso_values = sorted(
            list(map(lambda x: x[-1], self._isochrones_times)), reverse=True
        )
        iso_values_map: Dict = {
            x[0]: x[-1] for x in list(zip(iso_values, iso_values[1:]))
        }

        self._isochrones_built = []
        last_isochrone = None
        for iso_value_main_part, iso_value_part_to_remove in iso_values_map.items():
            # get main and part_to_remove isochrones
            iso_value_main_part_feature_idx = find_index(
                self._isochrones_data,
                self.__ISODISTANCE_NAME_FIELD,
                iso_value_main_part
            )
            iso_value_part_to_remove_feature_idx = find_index(
                self._isochrones_data,
                self.__ISODISTANCE_NAME_FIELD,
                iso_value_part_to_remove
            )

            iso_value_main_part_feature = self._isochrones_data[iso_value_main_part_feature_idx]
            iso_value_part_to_remove_feature = self._isochrones_data[iso_value_part_to_remove_feature_idx]

            # compute a raw isochrone
            isochrone_computed = iso_value_main_part_feature["geometry"].difference(
                iso_value_part_to_remove_feature["geometry"]
            )
            # add roads on the raw isochrone to respect isochrone area
            iso_value_main_part_roads_buffered = self._network_gdf.loc[
                self._network_gdf[self.__ISOCHRONE_NAME_FIELD] == iso_value_main_part_feature[
                    self.__ISOCHRONE_NAME_FIELD]
                ].buffer(
                self._display_mode_params["path_buffered"],
                resolution=self._display_mode_params["resolution"],
                cap_style=2
            ).unary_union
            iso_value_main_part_roads_buffered = MultiPolygon([
                iso_polygon_part
                for iso_polygon_part in convert_to_polygon(iso_value_main_part_roads_buffered)
            ])

            # remove water area
            isochrone_computed = isochrone_computed.difference(self._water_area)

            isochrone_computed = unary_union([isochrone_computed, iso_value_main_part_roads_buffered])

            # last_isochrone will be used to the next iteration to remove roads outside of the proceed isochrone
            if last_isochrone is not None:
                isochrone_computed = isochrone_computed.difference(last_isochrone)
            last_isochrone = isochrone_computed

            # we prepare the next isochrone, to be sure that it won't intersect the current isochrone
            next_iso_geom_udapted = iso_value_part_to_remove_feature["geometry"].difference(isochrone_computed)
            self._isochrones_data[iso_value_part_to_remove_feature_idx]["geometry"] = next_iso_geom_udapted

            # finalize
            for iso_polygon_part in convert_to_polygon(isochrone_computed):
                iso_value_main_part_feature_copy = dict(iso_value_main_part_feature)
                iso_value_main_part_feature_copy["geometry"] = iso_polygon_part
                self._isochrones_built.append(iso_polygon_part)
                self._output_data.append(iso_value_main_part_feature_copy)

        # should be the lowest, only 1
        isochrone_left = list(set(iso_values) - set(list(iso_values_map.keys())))
        assert len(isochrone_left) == 1
        last_iso_to_proceed_idx = find_index(
            self._isochrones_data,
            self.__ISODISTANCE_NAME_FIELD,
            isochrone_left[0]
        )
        last_iso_to_proceed_feature = self._isochrones_data[last_iso_to_proceed_idx]

        # get all isochrones to finish the last isochrone
        isochrones_to_remove = unary_union(self._isochrones_built)
        # compute the last isochrone
        isochrone_computed = last_iso_to_proceed_feature["geometry"].difference(isochrones_to_remove)

        for isochrone_geom in convert_to_polygon(isochrone_computed):
            last_iso_to_proceed_feature_copy = dict(last_iso_to_proceed_feature)
            last_iso_to_proceed_feature_copy["geometry"] = isochrone_geom
            self._output_data.append(last_iso_to_proceed_feature_copy)
