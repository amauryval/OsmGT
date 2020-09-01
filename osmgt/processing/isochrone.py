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

import math

from operator import itemgetter
import geopandas as gpd
import pandas as pd

try:
    from graph_tool.topology import extract_largest_component
    from graph_tool.topology import shortest_distance
except ModuleNotFoundError:
    pass

from shapely.wkt import loads
from shapely.geometry import base
from shapely.geometry import Point

from osmgt.geometry.geom_helpers import ConcaveHull
from osmgt.geometry.geom_helpers import reproject

# to facilitate debugging
try:
    from osmgt.network.gt_helper import GraphHelpers
except ModuleNotFoundError:
    pass


def split_multiline_to_lines(input_gdf, epsg_data):
    """
    split each linestring row from a geodataframe to point

    :param input_gdf: your geodataframe containing linestrings
    :type input_gdf: Geopandas.GeoDataframe
    :param epsg_data:
    :type epsg_data: str
    :return: your geodataframe exploded containing points
    :rtype: Pandas.Dataframe
    """

    # prepare indexed columns
    columns_index = input_gdf.columns.tolist()
    # without geometry column.. because we want explode it
    columns_index.remove("geometry")

    # convert the linestring to a list of points
    input_gdf["geometry"] = input_gdf["geometry"].apply(lambda x: x.geoms if x.geom_type == "MultiLineString" else x)
    # set index with columns_index variable (without geometry)
    input_gdf.set_index(columns_index, inplace=True)
    output = input_gdf["geometry"].explode().reset_index()
    # TODO add id with explode for each linestring created, and then MERGE based on topo_uuid
    geometry = output["geometry"]
    output: gpd.GeoDataFrame = gpd.GeoDataFrame(
        output.drop(["geometry"], axis=1),
        crs=f"EPSG:{epsg_data}",
        geometry=geometry.to_list(),
    )

    return output


class IsochroneArgError(Exception):
    pass


class OsmGtIsochrone(OsmGtRoads):

    __DISTANCE_TOLERANCE: float = 1.2
    __ISOCHRONE_NAME_FIELD: str = "iso_name"
    __ISODISTANCE_NAME_FIELD: str = "iso_distance"
    __DISSOLVE_NAME_FIELD: str = "__dissolve__"
    __TOPO_FIELD_REGEX_CLEANER = r"_[0-9]+$"

    def __init__(
        self,
        trip_speed: float,
        isochrones_times: Optional[List],
        distance_to_compute: Optional[List] = None,
    ) -> None:
        super().__init__()

        self.source_node: Optional[str] = None

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
            iso_time: math.ceil((iso_time * min_2_sec) * self._speed_to_m_s)  # distance
            for iso_time in isochrones_times
        }
        return self._compute_isochrones_ingredient(times_dist)

    def _prepare_isochrone_values_from_distance(
        self, distance_to_compute: List
    ) -> List:
        distance_to_compute.sort()

        times_dist: Dict = {
            distance / self._speed_to_m_s / min_2_sec: distance  # distance
            for distance in distance_to_compute
        }
        return self._compute_isochrones_ingredient(times_dist)

    def _compute_isochrones_ingredient(self, input_ingredients: Dict) -> List:

        times_dist: List = sorted(
            input_ingredients.items(), key=lambda x: x[1], reverse=True
        )
        return times_dist

    def from_location_point(
        self, location_point: Point, mode: str
    ) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:

        self.source_node = location_point.wkt
        # compute bbox
        max_distance = max(self._isochrones_times, key=itemgetter(1))[-1]
        location_point_reproj = reproject(location_point, epsg_4326, epsg_3857)
        location_point_reproj_buffered = location_point_reproj.buffer(
            max_distance * self.__DISTANCE_TOLERANCE
        )
        location_point_reproj_buffered_bounds = reproject(
            location_point_reproj_buffered, epsg_3857, epsg_4326
        ).bounds

        additionnal_nodes = [{self._TOPO_FIELD: 0, "geometry": location_point}]
        df = pd.DataFrame(additionnal_nodes)
        geometry = df["geometry"]
        additionnal_nodes_gdf = gpd.GeoDataFrame(
            df.drop(["geometry"], axis=1), crs=int(epsg_4326), geometry=geometry.to_list(),
        )
        self.from_bbox(
            location_point_reproj_buffered_bounds,
            additionnal_nodes=additionnal_nodes_gdf,
            mode=mode,
            interpolate_lines=True,
        )

        self._network_gdf = super().get_gdf()

        self._compute_isochrone()
        isochrones = self.get_gdf()

        return (
            isochrones,
            self._network_gdf[self._network_gdf[self.__ISOCHRONE_NAME_FIELD].notnull()],
        )

    def _compute_isochrone(self) -> None:
        graph = self.get_graph()
        source_vertex = graph.find_vertex_from_name(self.source_node)

        # reset output else isochrone will be append
        self._output_data = []

        for iso_time, dist in self._isochrones_times:
            pred = shortest_distance(
                graph,
                source=source_vertex,
                weights=graph.edge_weights,
                max_dist=dist,
                return_reached=True,
            )[1]

            points = [loads(graph.vertex_names[vertex]) for vertex in pred]

            concave_hull_proc = ConcaveHull(points)
            polygon = concave_hull_proc.polygon()

            network_gdf_copy_mask = self._network_gdf.within(polygon)

            isochrone_label = f"{iso_time} {time_unit}"

            self._network_gdf.loc[
                network_gdf_copy_mask, self.__ISOCHRONE_NAME_FIELD
            ] = isochrone_label
            self._network_gdf.loc[
                network_gdf_copy_mask, self.__ISODISTANCE_NAME_FIELD
            ] = dist

            self._output_data.append(
                {
                    self.__ISOCHRONE_NAME_FIELD: isochrone_label,
                    self.__ISODISTANCE_NAME_FIELD: dist,
                    "geometry": polygon,
                }
            )
        self.__dissolve_network_roads()

    def __dissolve_network_roads(self) -> None:
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

        # convert multilinestring to linestrings
        self._network_gdf = split_multiline_to_lines(self._network_gdf, epsg_4326)


    def get_gdf(self, verbose: bool = True) -> gpd.GeoDataFrame:
        output = super().get_gdf()
        # find iso index pair in order to create hole geom. isochrones are like russian dolls
        iso_values = sorted(list(map(lambda x: x[0], self._isochrones_times)), reverse=True)
        iso_values_map: Dict = {
            x[0]: x[-1] for x in list(zip(iso_values, iso_values[1:]))
        }
        output["geometry"] = output.apply(
            lambda x: self.__compute_isochrone_difference(
                x["geometry"],
                output.loc[
                    output[self.__ISOCHRONE_NAME_FIELD]
                    == iso_values_map[x[self.__ISOCHRONE_NAME_FIELD]]
                ].iloc[0]["geometry"],
            )
            if x[self.__ISOCHRONE_NAME_FIELD] in iso_values_map
            else x["geometry"],
            axis=1,
        )

        return output

    def __compute_isochrone_difference(
        self, first_geom: base, remove_part_geom: base
    ) -> base:

        return first_geom.difference(remove_part_geom)
