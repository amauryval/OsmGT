from typing import List

from typing import Union

import geopandas as gpd
from pyproj import Geod
from pyproj import Transformer

from shapely.ops import transform, linemerge

from shapely.geometry import base
from shapely.geometry import MultiLineString
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
    split each linestring row from a GeoDataframe to point

    :param input_gdf: your GeoDataframe containing LineStrings
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
        crs=f"EPSG:{epsg_data}",
        geometry=geometry.to_list(),
    )

    return output
