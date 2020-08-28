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
    from graph_tool.topology import shortest_distance
except ModuleNotFoundError:
    pass

from shapely.wkt import loads
from shapely.geometry import Point

from osmgt.geometry.geom_helpers import Concave_hull
from osmgt.geometry.geom_helpers import reproject


class OsmGtIsochrone(OsmGtRoads):

    __DISTANCE_TOLERANCE: float = 1.2
    __ISOCHRONE_NAME_FIELD: str = "iso_name"

    def __init__(self, isochrones_times: List, trip_speed: float) -> None:
        super().__init__()

        self.source_node: Optional[str] = None

        self._trip_speed: float = trip_speed  # km/h

        isochrones_times.sort()
        self._raw_isochrones = isochrones_times
        self._isochrones_times = self._prepare_isochrone_values(isochrones_times)

    def _prepare_isochrone_values(self, isochrones_times: List) -> List:
        speed_to_m_s: float = self._trip_speed / km_hour_2_m_sec

        times_reach_time_dist: Dict = {
            iso_time: math.ceil((iso_time * min_2_sec) * speed_to_m_s)  # distance
            for iso_time in isochrones_times
        }
        times_reach_time_dist_reversed: List = sorted(
            times_reach_time_dist.items(), key=lambda x: x[1], reverse=True
        )
        return times_reach_time_dist_reversed

    def from_location_point(self, location_point: Point, mode: str) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        self.source_node = location_point.wkt
        # compute bbox
        max_distance = max(self._isochrones_times , key=itemgetter(1))[-1]
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
            df.drop(["geometry"], axis=1), crs=4326, geometry=geometry.to_list(),
        )
        self.from_bbox(
            location_point_reproj_buffered_bounds,
            additionnal_nodes=additionnal_nodes_gdf,
            mode=mode,
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

            concave_hull_proc = Concave_hull(points)
            polygon = concave_hull_proc.polygon()

            network_gdf_copy_mask = self._network_gdf.within(polygon)

            isochrone_label = f"{iso_time} {time_unit}"

            self._network_gdf.loc[
                network_gdf_copy_mask, self.__ISOCHRONE_NAME_FIELD
            ] = isochrone_label

            self._output_data.append(
                {self.__ISOCHRONE_NAME_FIELD: isochrone_label, "geometry": polygon}
            )

    def get_gdf(self, verbose: bool = True) -> gpd.GeoDataFrame:
        output = super().get_gdf()
        # find iso index pair in order to create hole geom. isochrones are like russian dolls
        iso_values = self._raw_isochrones[::-1]
        iso_values_map = {x[0]: x[-1] for x in list(zip(iso_values, iso_values[1:]))}
        output["geometry"] = output.apply(
            lambda x: x["geometry"].difference(
                output.loc[
                    output[self.__ISOCHRONE_NAME_FIELD]
                    == iso_values_map[x[self.__ISOCHRONE_NAME_FIELD]]
                ].iloc[0]["geometry"]
            )
            if x[self.__ISOCHRONE_NAME_FIELD] in iso_values_map
            else x["geometry"],
            axis=1,
        )

        return output
