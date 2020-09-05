import warnings

import logging

from typing import Optional
from typing import List
from typing import Dict
from typing import Tuple

from osmgt.compoments.roads import OsmGtRoads

from osmgt.core.global_values import epsg_4326
from osmgt.core.global_values import epsg_3857
from osmgt.core.global_values import km_hour_2_m_sec
from osmgt.core.global_values import min_2_sec
from osmgt.core.global_values import time_unit
from osmgt.core.global_values import isochrone_display_mode

import math

from operator import itemgetter

import geopandas as gpd
import pandas as pd

import itertools

try:
    from graph_tool.topology import shortest_distance
except ModuleNotFoundError:
    pass

from shapely.wkt import loads
from shapely.geometry import base
from shapely.geometry import Point
from shapely.geometry import MultiPoint
from shapely.geometry import Polygon

from osmgt.geometry.geom_helpers import reprojection
from osmgt.geometry.geom_helpers import split_multiline_to_lines

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

    __DISTANCE_TOLERANCE: float = 1.5
    __ISOCHRONE_NAME_FIELD: str = "iso_name"
    __ISODISTANCE_NAME_FIELD: str = "iso_distance"
    __DISSOLVE_NAME_FIELD: str = "__dissolve__"
    __TOPO_FIELD_REGEX_CLEANER = r"_[0-9]+$"

    __CLEANING_NETWORK_BUFFER_VALUE: float = 0.000001
    __CLEANING_NETWORK_CAP_STYLE: int = 3
    __CLEANING_NETWORK_RESOLUTION: int = 4

    __DEFAULT_ISOCHRONE_CAPSTYLE = 1
    __DEFAULT_ISOCHRONE_JOINSTYLE = 1

    def __init__(
        self,
        trip_speed: float,
        isochrones_times: Optional[List],
        distance_to_compute: Optional[List] = None,
        display_mode: str = "orthogonal",
    ) -> None:
        super().__init__()
        self.logger.info("Isochrone processing...")

        self.__topo_uuids: List[str] = []
        self.source_node: Optional[str] = None
        self._isochrones_data: List[Dict] = []

        self._display_mode_params = isochrone_display_mode[display_mode]

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

        self._network_gdf = super().get_gdf()

        self._compute_isochrone()

        self._OUTPUT_EXPECTED_GEOM_TYPE = "Polygon"  # mandatory
        isochrones_gdf = self.get_gdf(verbose=False)

        return isochrones_gdf, self._network_gdf

    def _compute_isochrone(self) -> None:
        graph = self.get_graph()
        source_vertex = graph.find_vertex_from_name(self.source_node)

        # reset output else isochrone will be append
        self._output_data = []

        for iso_time, dist in self._isochrones_times:
            isochrone_label = f"{iso_time} {time_unit}"
            self.logger.info(f"Compute isochrone: {isochrone_label} => {dist} meters")

            _, pred = shortest_distance(
                graph,
                source=source_vertex,
                weights=graph.edge_weights,
                max_dist=dist,
                return_reached=True,
            )

            points = [graph.vertex_names[vertex] for vertex in pred]
            iso_polygon = MultiPoint(list(map(lambda x: loads(x), points))).convex_hull

            all_edges_found_topo_uuid = set(
                list(
                    itertools.chain(
                        *[graph.find_edges_from_vertex(pt) for pt in points]
                    )
                )
            )
            network_lines_candidates = self._network_gdf.loc[
                (self._network_gdf["topo_uuid"].isin(all_edges_found_topo_uuid))
                # | self._network_gdf.within(iso_polygon) # TODO improve isochrone
                # OR operator sometimes create a very minor error on isochrone results, it avoid some small network holes... cause by the convex hull polygon...
            ]["topo_uuid"].to_list()

            network_mask = self._network_gdf["topo_uuid"].isin(network_lines_candidates)
            self._network_gdf.loc[
                network_mask, self.__ISOCHRONE_NAME_FIELD
            ] = isochrone_label
            self._network_gdf.loc[network_mask, self.__ISODISTANCE_NAME_FIELD] = dist

            iso_polygon = Polygon(
                self._network_gdf.loc[network_mask]
                .buffer(
                    self._display_mode_params["path_buffered"],
                    cap_style=self.__DEFAULT_ISOCHRONE_CAPSTYLE,
                    join_style=self.__DEFAULT_ISOCHRONE_JOINSTYLE,
                    resolution=self._display_mode_params["resolution"],
                )
                # .buffer(0.00001, cap_style=2, join_style=3, resolution=8)
                #  only if buffer join_style = 2 => path needs to be rebuffered to connect them
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
                .exterior.coords
            )

            self._isochrones_data.append(
                {
                    self.__ISOCHRONE_NAME_FIELD: isochrone_label,
                    self.__ISODISTANCE_NAME_FIELD: dist,
                    "geometry": iso_polygon,
                }
            )
        self.__clean_isochrones()
        self.__clean_network()

    def __clean_network(self) -> None:
        self._network_gdf[self._TOPO_FIELD].replace(
            self.__TOPO_FIELD_REGEX_CLEANER, "", regex=True, inplace=True
        )

        self._network_gdf[self.__DISSOLVE_NAME_FIELD] = (
            self._network_gdf[self._TOPO_FIELD]
            + "__"
            + self._network_gdf[self.__ISOCHRONE_NAME_FIELD]
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

        gdf_copy = self._network_gdf.copy(deep=True)
        network_polygon = gdf_copy.buffer(
            self.__CLEANING_NETWORK_BUFFER_VALUE,
            cap_style=self.__CLEANING_NETWORK_CAP_STYLE,
            resolution=self.__CLEANING_NETWORK_RESOLUTION,
        ).unary_union
        if network_polygon.geom_type == "MultiPolygon":
            geom_areas = [(geom.area, geom) for geom in network_polygon.geoms]
            network_polygon = max(geom_areas)[-1]

        network_mask = self._network_gdf.within(network_polygon)
        self._network_gdf = self._network_gdf.loc[network_mask]

    def __clean_isochrones(self) -> None:
        # find iso index pair in order to create hole geom. isochrones are like russian dolls

        iso_values = sorted(
            list(map(lambda x: x[-1], self._isochrones_times)), reverse=True
        )
        iso_values_map: Dict = {
            x[0]: x[-1] for x in list(zip(iso_values, iso_values[1:]))
        }

        for iso_value_main_part, iso_value_part_to_remove in iso_values_map.items():

            iso_value_main_part_feature = list(
                filter(
                    lambda x: x[self.__ISODISTANCE_NAME_FIELD] == iso_value_main_part,
                    self._isochrones_data,
                )
            )

            iso_value_part_to_remove_feature = list(
                filter(
                    lambda x: x[self.__ISODISTANCE_NAME_FIELD]
                    == iso_value_part_to_remove,
                    self._isochrones_data,
                )
            )

            assert len(iso_value_main_part_feature) == 1
            assert len(iso_value_part_to_remove_feature) == 1
            iso_value_main_part_feature = iso_value_main_part_feature[0]
            iso_value_part_to_remove_feature = iso_value_part_to_remove_feature[0]

            isochrone_computed = self.__compute_isochrone_difference(
                iso_value_main_part_feature["geometry"],
                iso_value_part_to_remove_feature["geometry"],
            )
            isochrone_type = isochrone_computed.geom_type

            if isochrone_type == "MultiPolygon":
                for iso_polygon_part in isochrone_computed.geoms:
                    iso_value_main_part_feature_copy = dict(iso_value_main_part_feature)
                    iso_value_main_part_feature_copy["geometry"] = iso_polygon_part
                    self._output_data.append(iso_value_main_part_feature_copy)
            elif isochrone_type == "Polygon":
                iso_value_main_part_feature["geometry"] = isochrone_computed
                self._output_data.append(iso_value_main_part_feature)
            else:
                raise IsochroneGeomError(f"{isochrone_type} geom type not compatible")

        # should be the lowest, only 1
        isochrone_left = list(set(iso_values) - set(list(iso_values_map.keys())))
        assert len(isochrone_left) == 1
        iso_value_left_part_feature = list(
            filter(
                lambda x: x[self.__ISODISTANCE_NAME_FIELD] == isochrone_left[0],
                self._isochrones_data,
            )
        )
        for isochrone in iso_value_left_part_feature:
            isochrone["geometry"] = Polygon(isochrone["geometry"].exterior.coords)
            self._output_data.append(isochrone)

    @staticmethod
    def __compute_isochrone_difference(
        first_geom: base, remove_part_geom: base
    ) -> base:

        return first_geom.difference(remove_part_geom)
