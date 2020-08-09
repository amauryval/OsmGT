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
        return OsmGtRoads().from_bbox(bbox_value, additionnal_nodes, mode)

    @staticmethod
    def roads_from_gdf(input_gdf, additionnal_nodes=None, mode="vehicle"):
        return OsmGtRoads().from_gdf(input_gdf, additionnal_nodes, mode)

    @staticmethod
    def poi_from_location(location_name):
        return OsmGtPoi().from_location(location_name)

    @staticmethod
    def poi_from_bbox(bbox_value):
        return OsmGtPoi().from_bbox(bbox_value)
