from osmgt.compoments.roads import OsmGtRoads

from itertools import chain

import geopandas as gpd
import pandas as pd

try:
    from graph_tool.topology import shortest_path
except:
    pass

from shapely.geometry import LineString
from shapely.ops import linemerge


def multilinestring_continuity(linestrings):

    """
    :param linestrings: linestring with different orientations, directed with the last coords of the first element
    :type linestrings: list of shapely.geometry.MultiLineString
    :return: re-oriented MultiLineSting
    :rtype: shapely.geometry.MultiLineString
    """

    dict_line = {key: value for key, value in enumerate(linestrings)}
    for key, line in dict_line.items():
        if key != 0 and dict_line[key - 1].coords[-1] == line.coords[-1]:
            dict_line[key] = LineString(line.coords[::-1])
    return [v for _, v in dict_line.items()]


class OsmGtShortestPath(OsmGtRoads):

    def __init__(self, source_target_points):
        super().__init__()

        self._source_target_points = source_target_points
        self._all_points = chain(*source_target_points)

        self._graph = None
        self._gdf = None
        self._additionnal_nodes_gdf = self._prepare_nodes()

    def _prepare_nodes(self):

        additionnal_nodes = [
            {self._TOPO_FIELD: enum, "geometry": geom}
            for enum, geom in enumerate(self._all_points)
        ]
        df = pd.DataFrame(additionnal_nodes)
        geometry = df["geometry"]
        additionnal_nodes_gdf = gpd.GeoDataFrame(
            df.drop(["geometry"], axis=1),
            crs=4326,
            geometry=geometry.to_list(),
        )

        return additionnal_nodes_gdf

    def from_location(self, location_name, additionnal_nodes=None, mode="pedestrian"):
        super().from_location(location_name, additionnal_nodes=self._additionnal_nodes_gdf, mode=mode)
        self._compute_data_and_graph()

        return self.get_gdf()

    def from_bbox(self, bbox_value, additionnal_nodes=None, mode="pedestrian"):
        super().from_bbox(bbox_value, additionnal_nodes, mode)
        self._compute_data_and_graph()

        return self.get_gdf()

    def _compute_data_and_graph(self):
        self._graph = super().get_graph()
        self._gdf = self.get_gdf()

        self._output_data = []
        # todo multithread it!
        for source_node, target_node in self._source_target_points:
            self._compute_shortest_path(source_node, target_node)

        return self.get_gdf()

    def _compute_shortest_path(self, source_node, target_node):

        source_vertex = self._graph.find_vertex_from_name(source_node.wkt)
        target_vertex = self._graph.find_vertex_from_name(target_node.wkt)

        self.logger.info(f"Compute path from {source_vertex} to {target_vertex}")

        # shortest path computing...
        _, path_edges = shortest_path(
            self._graph,
            source=source_vertex,
            target=target_vertex,
            weights=self._graph.edge_weights  # weights is based on line length
        )

        gdf_copy = self._gdf.copy(deep=True)
        # # get path by using edge names
        path_geoms = gdf_copy[
            gdf_copy['topo_uuid'].isin([self._graph.edge_names[edge] for edge in path_edges])
        ]["geometry"].to_list()

        self._output_data.append(
            {
                "source_node": source_node,
                "target_node": target_node,
                "geometry":  linemerge(path_geoms)
            }
        )



