from pyproj import Geod

from shapely.ops import cascaded_union
from shapely.ops import polygonize
from shapely.geometry import MultiLineString
from shapely.geometry import MultiPoint
from scipy.spatial import Delaunay
import numpy as np
import math

def compute_wg84_line_length(input_geom):
    """
    Compute the length of a wg84 line (LineString and MultiLineString)

    :param input_geom: input geometry
    :type input_geom: shapely.geometry.LineString or shapely.geometry.MultiLineString
    :return: the line length
    :rtype: float

    """
    total_length = 0

    if input_geom.geom_type == "MultiLineString":
        for geom_line in input_geom.geoms:
            total_length += compute_wg84_line_length(geom_line)

    elif input_geom.geom_type == "LineString":
        coordinates_pairs = list(zip(input_geom.coords, input_geom.coords[1:]))
        for pair in coordinates_pairs:

            if len(pair[0]) == 3 or len(pair[1]) == 3:
                coords = pair[0][:-1] + pair[1][:-1]  # avoid to catch the elevation coord
            else:
                coords = pair[0] + pair[1]

            wgs84_geod = Geod(ellps='WGS84')
            _, _, length_computed = wgs84_geod.inv(*coords)
            total_length += length_computed

    return total_length


class Concave_hull:
    # source: http://blog.thehumangeo.com/2014/05/12/drawing-boundaries-in-python/
    __TOLERANCE_VALUE = 1.87

    # Do not change values
    __SQUARED_VALUE = 2
    __SEMIPERIMETER_DIVISOR = 2
    __HERON_FORMULA_DIVISOR = 4
    __MIN_NUMBER_OF_POINTS = 4

    def __init__(self , points):
        """
        :param points: list of shapely points
        :type: list of shapely point
        """
        self._points = points

        self.__edges = set()
        self.edge_points = []

    def run(self):
        result = self._check_points_number()

        if result is None:
            coords = np.array([point.coords[0] for point in self._points])
            triangulation = Delaunay(coords)
            # loop over triangles:
            # ia, ib, ic = indices of corner points of the
            # triangle
            for ia , ib , ic in triangulation.vertices:
                pa = coords[ia]
                pb = coords[ib]
                pc = coords[ic]

                # Lengths of sides of triangle
                a = math.sqrt((pa[0] - pb[0]) ** self.__SQUARED_VALUE + (pa[1] - pb[1]) ** self.__SQUARED_VALUE)
                b = math.sqrt((pb[0] - pc[0]) ** self.__SQUARED_VALUE + (pb[1] - pc[1]) ** self.__SQUARED_VALUE)
                c = math.sqrt((pc[0] - pa[0]) ** self.__SQUARED_VALUE + (pc[1] - pa[1]) ** self.__SQUARED_VALUE)

                # Semiperimeter of triangle
                s = (a + b + c) / self.__SEMIPERIMETER_DIVISOR

                # Area of triangle by Heron's formula
                area = math.sqrt(s * (s - a) * (s - b) * (s - c))
                circum_r = a * b * c / (self.__HERON_FORMULA_DIVISOR * area)

                # Here's the radius filter.
                if circum_r < 1.0 / self.__TOLERANCE_VALUE:
                    self.add_edge(coords, ia, ib)
                    self.add_edge(coords, ib, ic)
                    self.add_edge(coords, ic, ia)

            multilinestring_built = MultiLineString(self.edge_points)
            triangles = list(polygonize(multilinestring_built))
            return cascaded_union(triangles)

    def _check_points_number(self):
        if len(self._points) < self.__MIN_NUMBER_OF_POINTS:
            return MultiPoint(self._points).convex_hull

    def add_edge(self, coords , i, j):
        """
        Add a line between the i-th and j-th points,
        if not in the list already
        """
        if (i, j) in self.__edges or (j, i) in self.__edges:
            # already added
            return
        self.__edges.add((i , j))
        self.edge_points.append(coords[[i, j]])
