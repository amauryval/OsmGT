from osgeo import ogr
from osgeo import osr
from shapely.wkt import loads
from shapely.geometry import base


def ogr_reproject(geometry, from_epsg, to_epsg):
    """
    ogr_reprojection

    :type geometry: shapely.geometry.*
    :type from_epsg: int
    :type to_epsg: int
    :rtype: shapely.geometry.*
    """
    assert isinstance(from_epsg, int), "from_epsg arg should be an integer"
    assert isinstance(to_epsg, int), "to_epsg arg should be an integer"

    if from_epsg != to_epsg:
        source_epsg = osr.SpatialReference()
        source_epsg.ImportFromEPSG(from_epsg)

        target_epsg = osr.SpatialReference()
        target_epsg.ImportFromEPSG(to_epsg)

        epsg_transform = osr.CoordinateTransformation(source_epsg, target_epsg)
        ogr_geom = ogr.CreateGeometryFromWkt(geometry.wkt)
        ogr_geom.Transform(epsg_transform)
        geometry = loads(ogr_geom.ExportToWkt())

    return geometry
