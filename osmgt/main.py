import geopandas as gpd
from shapely.geometry import Point

from osmgt.compoments.roads import OsmGtRoads
from osmgt.compoments.poi import OsmGtPoi

from osmgt.processing.isochrone import OsmGtIsochrone
from osmgt.processing.shortest_path import OsmGtShortestPath

from typing import Tuple
from typing import List
from typing import Optional


class OsmGt:
    @staticmethod
    def roads_from_location(
        location_name: str,
        mode: str = "pedestrian",
        additionnal_nodes: Optional[gpd.GeoDataFrame] = None,
    ) -> OsmGtRoads:
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
        osm_road = OsmGtRoads()
        osm_road.from_location(location_name, additionnal_nodes, mode)
        return osm_road

    @staticmethod
    def roads_from_bbox(
        bbox_values: Tuple[float, float, float, float],
        mode: str = "pedestrian",
        additionnal_nodes: Optional[gpd.GeoDataFrame] = None,
    ) -> OsmGtRoads:
        """
        Get OpenStreetMap roads from a bbox

        :param bbox_values: a bbox value : (minx , miny , maxx , maxy) or (min_lng, min_lat, max_lng, max_lat)
        :type bbox_values: tuple of float
        :param mode: the transport mode
        :type mode: str, default 'pedestrian', one of : pedestrian, vehicle
        :param additionnal_nodes: Addtionnals nodes to connect on the network
        :type additionnal_nodes: geopandas.GeoDataFrame
        :return: OsmGtRoads class
        :rtype: OsmGtRoads
        """
        osm_road = OsmGtRoads()
        osm_road.from_bbox(bbox_values, additionnal_nodes, mode)
        return osm_road

    @staticmethod
    def poi_from_location(location_name: str) -> OsmGtPoi:
        """
        Find OSM POIs from a location name

        :param location_name: a location name
        :type location_name: str
        :return: OsmGtRoads class
        :rtype: OsmGtRoads
        """
        osm_poi = OsmGtPoi()
        osm_poi.from_location(location_name)
        return osm_poi

    @staticmethod
    def poi_from_bbox(bbox_values: Tuple[float, float, float, float]) -> OsmGtPoi:
        """
        Find OSM POIs from a bbox value

        :param bbox_values: a bbox value : (minx , miny , maxx , maxy) or (min_lng, min_lat, max_lng, max_lat)
        :type bbox_values: tuple of float
        :return: OsmGtRoads class
        :rtype: OsmGtRoads
        """
        osm_poi = OsmGtPoi()
        osm_poi.from_bbox(bbox_values)
        return osm_poi

    @staticmethod
    def isochrone_from_coordinates(
        coordinates: Point,
        isochrones_times: List[float],
        trip_speed: float,
        mode: str = "pedestrian",
    ) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
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

        isochrone_polygons_gdf, isochrone_lines_gdf = OsmGtIsochrone(
            trip_speed, isochrones_times
        ).from_location_point(coordinates, mode)

        return isochrone_polygons_gdf, isochrone_lines_gdf

    @staticmethod
    def isochrone_distance_from_coordinates(
        coordinates: Point,
        distances: List,
        trip_speed: float,
        mode: str = "pedestrian",
    ) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        """
        :param coordinates: location points
        :type coordinates: shapely.geometry.Point
        :param distances: distances (meters)
        :type distances: list of int
        :param trip_speed: trip speed in km/h
        :type trip_speed: int
        :param mode: the transport mode
        :type mode: str, default 'pedestrian', one of : pedestrian, vehicle
        :return: 2 geodataframe : isochrones polygons and isochrones lines (roads)
        :rtype: tuple(geopandas.GeoDataFrame)
        """

        isochrone_polygons_gdf, isochrone_lines_gdf = OsmGtIsochrone(
            trip_speed, None, distances
        ).from_location_point(coordinates, mode)

        return isochrone_polygons_gdf, isochrone_lines_gdf

    @staticmethod
    def shortest_path_from_location(
        location_name: str,
        source_target_points: List[Tuple[Point, Point]],
        mode: str = "pedestrian",
    ) -> gpd.GeoDataFrame:
        """

        :param location_name: the name of the location
        :type location_name: the name of the location
        :param source_target_points: list of tuple source and target points
        :type source_target_points: list of tuple (shapely.geometry.Point)
        :param mode: the transport mode
        :type mode: str, default 'pedestrian', one of :
        :return: geodataframe containing all the shortest paths
        :rtype: geopandas.GeoDataFrame
        """

        return OsmGtShortestPath(source_target_points).from_location(
            location_name, None, mode
        )

    @staticmethod
    def shortest_path_from_bbox(
        bbox_values: Tuple[float, float, float, float],
        source_target_points: List[Tuple[Point, Point]],
        mode: str = "pedestrian",
    ) -> gpd.GeoDataFrame:
        """

        :param bbox_values: a bbox value : (minx , miny , maxx , maxy) or (min_lng, min_lat, max_lng, max_lat)
        :type bbox_values: tuple of float
        :param source_target_points: list of tuple source and target points
        :type source_target_points: list of tuple (shapely.geometry.Point)
        :param mode: the transport mode
        :type mode: str, default 'pedestrian', one of :
        :return: geodataframe containing all the shortest paths
        :rtype: geopandas.GeoDataFrame
        """

        return OsmGtShortestPath(source_target_points).from_bbox(
            bbox_values, None, mode
        )
