from osmgt.compoments.roads import OsmGtRoads
from osmgt.compoments.poi import OsmGtPoi

class OsmGt:

    @staticmethod
    def roads_from_location(location_name, mode="pedestrian", additionnal_nodes=None):
        """
        Get OpenStreetMap roads from a location name

        :param location_name: the name of the location
        :type location_name: the name of the location
        :param mode: the transport mode
        :type mode: str, default 'pedestrian', one of :
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
        :type mode: str, default 'pedestrian', one of :
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

