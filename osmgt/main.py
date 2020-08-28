from osmgt.compoments.roads import OsmGtRoads
from osmgt.compoments.poi import OsmGtPoi

from osmgt.processing.isochrone import OsmGtIsochrone
from osmgt.processing.shortest_path import OsmGtShortestPath

from typing import *

class OsmGt:
    @staticmethod
    def roads_from_location(location_name, mode="pedestrian", additionnal_nodes=None):
        """
        Get OpenStreetMap roads from a location name

        :param location_name: the name of the location
        :type location_name: the name of the location
        :param mode: the transport mode
        :type mode: str, default 'pedestrian', one of : pedestrian, vehicle
        :param additionnal_nodes: Addtionnals nodes to connect on the network
        :type additionnal_nodes: geopandas.GeoDataFrame
        :return: OsmGtRoads class
        :rtype: OsmGtRoads
        """

        return OsmGtRoads().from_location(location_name, additionnal_nodes, mode)

    @staticmethod
    def roads_from_bbox(bbox_value, mode="pedestrian", additionnal_nodes=None):
        """
        Get OpenStreetMap roads from a bbox

        :param bbox_value: a bbox value : (minx , miny , maxx , maxy) or (min_lng, min_lat, max_lng, max_lat)
        :type bbox_value: tuple of float
        :param mode: the transport mode
        :type mode: str, default 'pedestrian', one of : pedestrian, vehicle
        :param additionnal_nodes: Addtionnals nodes to connect on the network
        :type additionnal_nodes: geopandas.GeoDataFrame
        :return: OsmGtRoads class
        :rtype: OsmGtRoads
        """
        return OsmGtRoads().from_bbox(bbox_value, additionnal_nodes, mode)

    @staticmethod
    def poi_from_location(location_name):
        """
        Find OSM POIs from a location name

        :param location_name: a location name
        :type location_name: str
        :return: OsmGtRoads class
        :rtype: OsmGtRoads
        """
        return OsmGtPoi().from_location(location_name)

    @staticmethod
    def poi_from_bbox(bbox_value):
        """
        Find OSM POIs from a bbox value

        :param bbox_value: a bbox value : (minx , miny , maxx , maxy) or (min_lng, min_lat, max_lng, max_lat)
        :type bbox_value: tuple of float
        :return: OsmGtRoads class
        :rtype: OsmGtRoads
        """
        return OsmGtPoi().from_bbox(bbox_value)

    @staticmethod
    def isochrone_from_coordinates(
        coordinates, isochrones_times, trip_speed, mode="pedestrian"
    ):
        """
        :param coordinates: location points
        :type coordinates: shapely.geometry.Point
        :param isochrones_times: isochrones to build (in minutes)
        :type isochrones_times: list of int
        :param trip_speed: trip speed in km/h
        :type trip_speed: int
        :param mode: the transport mode
        :type mode: str, default 'pedestrian', one of : pedestrian, vehicle
        :return: 2 geodataframe : isochrones polygons and isochrones lines (roads)
        :rtype: tuple(geopandas.GeoDataFrame)
        """

        isochrone_polygons_gdf, isochrone_lines_gdf = OsmGtIsochrone(isochrones_times, trip_speed).from_location_point(
            coordinates, mode
        )

        return isochrone_polygons_gdf, isochrone_lines_gdf

    @staticmethod
    def shortest_path_from_location(
        location_name, source_target_points, mode="pedestrian"
    ):
        """

        :param location_name: the name of the location
        :type location_name: the name of the location
        :param source_target_points: list of tuple source and target points
        :type source_target_points: list of tuple (shapely.geometry.Point)
        :param mode: the transport mode
        :type mode: str, default 'pedestrian', one of :
        :return: geodataframe containing the shortest path
        :rtype: geopandas.GeoDataFrame
        """

        return OsmGtShortestPath(source_target_points).from_location(
            location_name, mode
        )
