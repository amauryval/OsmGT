from osmgt.compoments.roads import OsmGtRoads

import math

from operator import itemgetter
import geopandas as gpd
import pandas as pd

try:
    from graph_tool.topology import shortest_distance
except:
    pass

from shapely.wkt import loads
from osmgt.geometry.geom_helpers import Concave_hull
from osmgt.geometry.geom_helpers import reproject


class OsmGtIsochrone(OsmGtRoads):

    __KM_SEC_2_M_SEC = 3.6
    __SECS_IN_MIN = 60
    __DISTANCE_TOLERANCE = 1.2
    __BUFFER_VALUE_FOR_SMOOTHING = 0.001

    def __init__(self, isochrones_to_build, trip_speed=3):
        super().__init__()

        self.source_node = None

        self._trip_speed = trip_speed  # km/h
        self._isochrones_to_build = self._prepare_isochrone_values(isochrones_to_build)

    def _prepare_isochrone_values(self, isochrones_to_build):
        speed_to_m_s = self._trip_speed / self.__KM_SEC_2_M_SEC
        times_reach_time_dist = {
            t: math.ceil((t * self.__SECS_IN_MIN) * speed_to_m_s)
            for t in isochrones_to_build
        }
        times_reach_time_dist_reversed = sorted(times_reach_time_dist.items(), key=lambda x: x[1], reverse=True)
        return times_reach_time_dist_reversed

    def from_location_point(self, location_point, mode):
        self.source_node = location_point.wkt
        # compute bbox
        max_distance = max(self._isochrones_to_build, key=itemgetter(1))[-1]
        location_point_reproj = reproject(location_point, 4326, 3857)
        location_point_reproj_buffered = location_point_reproj.buffer(max_distance * self.__DISTANCE_TOLERANCE)
        location_point_reproj_buffered_bounds = reproject(location_point_reproj_buffered, 3857, 4326).bounds

        additionnal_nodes = [{self._TOPO_FIELD: 0, "geometry": location_point}]
        df = pd.DataFrame(additionnal_nodes)
        geometry = df["geometry"]
        additionnal_nodes_gdf = gpd.GeoDataFrame(
            df.drop(["geometry"], axis=1),
            crs=4326,
            geometry=geometry.to_list(),
        )
        self.from_bbox(location_point_reproj_buffered_bounds, additionnal_nodes=additionnal_nodes_gdf, mode=mode)
        self._compute_isochrone()

        return self.get_gdf()

    def _compute_isochrone(self):
        graph = self.get_graph()
        source_vertex = graph.find_vertex_from_name(self.source_node)

        # reset output else isochrone will be append
        self._output_data = []

        for t, dist in self._isochrones_to_build:
            pred = shortest_distance(
                graph,
                source=source_vertex,
                weights=graph.edge_weights,
                max_dist=dist,
                return_reached=True,
            )[1]
            print(len(pred))
            points = [
                loads(graph.vertex_names[vertex])
                for vertex in pred
            ]
            #     concave_hull, edge_points = alpha_shape(points, alpha=1.87)
            concave_hull = Concave_hull(points).run()
            self._output_data.append({
                "iso_name": t,
                "geometry": concave_hull.buffer(self.__BUFFER_VALUE_FOR_SMOOTHING),
                #         "geometry": MultiPoint(points)
            })