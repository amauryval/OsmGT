from shapely.geometry import Point
from shapely.geometry import MultiPoint
from shapely.geometry import LineString
from shapely.geometry import LinearRing
from shapely.geometry import MultiLineString
from shapely.geometry import Polygon
from shapely.geometry.polygon import InteriorRingSequence
from shapely.geometry import MultiPolygon
from shapely.geometry import GeometryCollection


def geometry_2_bokeh_format(geometry, coord_name="xy"):
    """
    geometry_2_bokeh_format
    Used for bokeh library

    :type geometry: shapely.geometry.*
    :type coord_name: str, default: xy (x or y)
    :return: float or list of tuple
    """
    coord_values = []
    if isinstance(geometry, Point):
        if coord_name != "xy":
            coord_values = getattr(geometry, coord_name)
        else:
            coord_values = next(iter(geometry.coords))

    elif isinstance(geometry, Polygon):
        exterior = [
            geometry_2_bokeh_format(geometry.exterior, coord_name)
        ]
        interiors = geometry_2_bokeh_format(
            geometry.interiors, coord_name
        )
        coord_values = [exterior, interiors]
        if len(interiors) == 0:
            coord_values = [exterior]

    elif isinstance(geometry, (LinearRing, LineString)):
        coord_values = [
            geometry_2_bokeh_format(Point(feat), coord_name)
            for feat in geometry.coords
        ]

    if isinstance(geometry, (MultiPoint, MultiPolygon, MultiLineString)):
        for feat in geometry.geoms:
            if isinstance(feat, Point):
                coord_values = geometry_2_bokeh_format(feat, coord_name)
            else:
                coord_values.extend(
                    geometry_2_bokeh_format(feat, coord_name)
                )

    if isinstance(geometry, InteriorRingSequence):
        # compute holes
        coord_values.extend(
            [
                geometry_2_bokeh_format(feat, coord_name)
                for feat in geometry
            ]
        )

    if isinstance(geometry, GeometryCollection):
        raise ValueError("no interest to handle GeometryCollection")

    return coord_values