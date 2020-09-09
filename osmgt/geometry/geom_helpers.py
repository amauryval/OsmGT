from typing import List
from typing import Union
from typing import Optional
from typing import Tuple
from typing import Set

import geopandas as gpd

from pyproj import Geod
from pyproj import Transformer

from shapely.ops import transform
from shapely.ops import linemerge
from shapely.ops import unary_union
from shapely.ops import polygonize

from shapely.geometry import base
from shapely.geometry import LineString
from shapely.geometry import Point
from shapely.geometry import MultiPoint
from shapely.geometry import MultiLineString

from scipy.spatial import Delaunay

import numpy as np

import math


def compute_wg84_line_length(input_geom: Union[LineString, MultiLineString]) -> float:
    """
    Compute the length of a wg84 line (LineString and MultiLineString)

    :param input_geom: input geometry
    :type input_geom: shapely.geometry.LineString or shapely.geometry.MultiLineString
    :return: the line length
    :rtype: float

    """

    line_length = Geod(ellps="WGS84").geometry_length(input_geom)

    return line_length


def reprojection(geometry: base, from_epsg: str, to_epsg: str) -> base:
    """
    reprojection

    :type geometry: shapely.geometry.*
    :type from_epsg: int
    :type to_epsg: int
    :rtype: shapely.geometry.*
    """

    if from_epsg != to_epsg:
        proj_transformer = Transformer.from_crs(
            f"EPSG:{from_epsg}", f"EPSG:{to_epsg}", always_xy=True
        )
        geometry = transform(proj_transformer.transform, geometry)

    return geometry


def line_conversion(
    input_geometry: Union[LineString, MultiLineString]
) -> Union[LineString, List[LineString]]:

    if input_geometry.geom_type == "LineString":
        return [input_geometry]
    elif input_geometry.geom_type == "MultiLineString":
        line_merged = linemerge([line_geom for line_geom in input_geometry.geoms])
        if line_merged.geom_type == "LineString":
            return [line_merged]
        elif line_merged.geom_type == "MultiLineString":
            return line_merged.geoms
        else:
            raise TypeError(f"Geometry type unexpected: {line_merged.geom_type}")


def split_multiline_to_lines(
    input_gdf: gpd.GeoDataFrame, epsg_data: str, id_field: str
) -> gpd.GeoDataFrame:
    """
    Convert MultiLinestring GeoDataframe rows to LineString rows

    :param input_gdf: GeoDataframe containing MultiLineStrings or LineString
    :type input_gdf: Geopandas.GeoDataframe
    :param epsg_data:
    :type epsg_data: str
    :param id_field:
    :type id_field: str
    :return: your GeoDataframe exploded containing points
    :rtype: Pandas.Dataframe
    """

    # prepare indexed columns
    columns_index = input_gdf.columns.tolist()
    # without geometry column.. because we want explode it
    columns_index.remove("geometry")

    # convert the linestring to a list of points
    input_gdf["geometry"] = input_gdf["geometry"].apply(lambda x: line_conversion(x))
    # set index with columns_index variable (without geometry)
    input_gdf.set_index(columns_index, inplace=True)
    output = input_gdf["geometry"].explode().reset_index()
    output[id_field] = output[id_field] + output.index.map(str)
    geometry = output["geometry"]
    output: gpd.GeoDataFrame = gpd.GeoDataFrame(
        output.drop(["geometry"], axis=1),
        geometry=geometry.to_list(),
        crs=f"EPSG:{epsg_data}",
    )

    return output


def split_linestring_to_points(
    input_gdf: gpd.GeoDataFrame, epsg_data: str, positions: list = [0, -1]
) -> gpd.GeoDataFrame:
    """
    split each Linestring GeoDataframe rows to points rows

    :param input_gdf: GeoDataframe containing LineStrings
    :type input_gdf: Geopandas.GeoDataframe
    :param epsg_data: epsg value
    :type epsg_data: str
    :param positions: list containing point index position to filter
    :type positions: list of int
    :return: your GeoDataframe exploded containing points
    :rtype: Pandas.Dataframe
    """
    columns_without_geometry = input_gdf.columns.tolist()
    columns_without_geometry.remove("geometry")

    input_gdf_copy = input_gdf.copy(deep=True)

    input_gdf_copy["geometry"] = input_gdf_copy["geometry"].apply(
        lambda geom: [Point(geom.coords[pos]) for pos in positions]
    )

    input_gdf_copy.set_index(columns_without_geometry, inplace=True)
    output = input_gdf_copy["geometry"].explode().reset_index()
    geometry = output["geometry"]
    output = gpd.GeoDataFrame(
        output.drop(["geometry"], axis=1),
        geometry=geometry.to_list(),
        crs=f"EPSG:{epsg_data}",
    )

    return output


class ConcaveHull:
    # source: https://sgillies.net/2012/10/13/the-fading-shape-of-alpha.html

    # Do not change values
    __SQUARED_VALUE: int = 2
    __SEMIPERIMETER_DIVISOR: int = 2
    __HERON_FORMULA_DIVISOR: int = 4
    __MIN_NUMBER_OF_POINTS: int = 4

    def __init__(self, points: List[Point], alpha=0.5):
        """
        :param points: list of shapely points
        :type: list of shapely point
        """
        self._points = points
        self._alpha = alpha

        self.__edges: Set[Tuple[float, float]] = set()
        self._edge_points: List[Tuple[Tuple[float, float]]] = []  # TODO check type
        self._compute()

    def _compute(self) -> None:
        result: Optional[MultiPoint] = self._check_points_number()

        if result is None:
            coords = np.array([point.coords[0] for point in self._points])
            triangulation = Delaunay(coords)
            # loop over triangles:
            # ia, ib, ic = indices of corner points of the
            # triangle
            for ia, ib, ic in triangulation.vertices:
                pa = coords[ia]
                pb = coords[ib]
                pc = coords[ic]

                # Lengths of sides of triangle
                a = math.sqrt(
                    (pa[0] - pb[0]) ** self.__SQUARED_VALUE
                    + (pa[1] - pb[1]) ** self.__SQUARED_VALUE
                )
                b = math.sqrt(
                    (pb[0] - pc[0]) ** self.__SQUARED_VALUE
                    + (pb[1] - pc[1]) ** self.__SQUARED_VALUE
                )
                c = math.sqrt(
                    (pc[0] - pa[0]) ** self.__SQUARED_VALUE
                    + (pc[1] - pa[1]) ** self.__SQUARED_VALUE
                )

                # Semiperimeter of triangle
                s = (a + b + c) / self.__SEMIPERIMETER_DIVISOR

                # Area of triangle by Heron's formula
                delta = s * (s - a) * (s - b) * (s - c)
                if delta > 0:
                    area = math.sqrt(delta)
                    if area > 0:
                        circum_r = a * b * c / (self.__HERON_FORMULA_DIVISOR * area)

                        # Here's the radius filter.
                        if circum_r < 1.0 / self._alpha:
                            self.add_edge(coords, ia, ib)
                            self.add_edge(coords, ib, ic)
                            self.add_edge(coords, ic, ia)

            multilinestring_built = MultiLineString(self._edge_points)
            self._triangles: List = list(polygonize(multilinestring_built))

    def polygon(self):
        return unary_union(self._triangles)

    def points(self) -> List:
        return self._edge_points

    def _check_points_number(self) -> Optional[MultiPoint]:
        if len(self._points) < self.__MIN_NUMBER_OF_POINTS:
            return MultiPoint(self._points).convex_hull

    def add_edge(self, coords, i: float, j: float) -> None:
        """
        Add a line between the i-th and j-th points,
        if not in the list already
        """
        if (i, j) in self.__edges or (j, i) in self.__edges:
            # already added
            return
        self.__edges.add((i, j))
        self._edge_points.append(coords[[i, j]])


def convert_to_polygon(polygon_geom):
    output_polygons = []

    isochrone_type = polygon_geom.geom_type
    if isochrone_type == "Polygon":
        output_polygons.append(polygon_geom)

    elif isochrone_type == "MultiPolygon":
        for polygon_part in polygon_geom.geoms:
            output_polygons.append(polygon_part)
    else:
        raise TypeError(f"{isochrone_type} geom type not compatible")

    return output_polygons
