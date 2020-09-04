from typing import List

from typing import Union

import geopandas as gpd
from pyproj import Geod
from pyproj import Transformer

from shapely.ops import transform
from shapely.ops import linemerge
from shapely.ops import split

from shapely.geometry import base
from shapely.geometry import MultiLineString
from shapely.geometry import Point

from shapely.geometry import Polygon
from shapely.geometry import LineString


def compute_wg84_line_length(input_geom: LineString) -> float:
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
                coords = (
                    pair[0][:-1] + pair[1][:-1]
                )  # avoid to catch the elevation coord
            else:
                coords = pair[0] + pair[1]

            wgs84_geodetic = Geod(ellps="WGS84")
            _, _, length_computed = wgs84_geodetic.inv(*coords)
            total_length += length_computed

    return total_length


def reprojection(geometry: base, from_epsg: int, to_epsg: int) -> base:
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
    :param epsg_data:
    :type epsg_data: str
    :param id_field:
    :type id_field: str
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


def snap_polygon_to_nearest_points(polygon, points):
    """

    :param polygon:
    :param points:
    :return:

    polygon = Polygon([(1,1), (2, 1), (2, 2), (1, 2), (1, 1)])
    points = [Point(1.3, 1.4)]
    snap_polygon_to_nearest_points(polygon, points)
    """

    linearing_coordinates = polygon.exterior.coords[:]
    linestrings_built = list(map(
        lambda x: LineString(x), list(zip(linearing_coordinates, linearing_coordinates[1:]))
    ))

    for point in points:
        _, line_pos = min([
            (point.distance(line), pos)
            for pos, line in enumerate(linestrings_built)
        ])
        line_found = linestrings_built[line_pos]

        # create a twin node into the line found
        end_point = line_found.interpolate(line_found.project(point))
        line_updated = split(line_found, end_point)
        line_updated = linemerge(line_updated.geoms)

        # find the position of the twin coordinate
        line_updated_coordinates = line_updated.coords[:]
        end_point_position = line_updated_coordinates.index(end_point.coords[0])
        line_updated_coordinates[end_point_position] = point.coords[0]

        linestrings_built[line_pos] = LineString(line_updated_coordinates)

    # linestrings to polygon
    return Polygon(linemerge(linestrings_built))
