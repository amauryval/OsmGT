from osmgt.compoments.roads import OsmGtRoads
from osmgt.compoments.poi import OsmGtPoi


class OsmGt:

    @staticmethod
    def roads_from_location(location_name, additionnal_nodes=None):
        return OsmGtRoads().from_location(location_name, additionnal_nodes)

    @staticmethod
    def roads_from_bbox(bbox_value, additionnal_nodes=None):
        return OsmGtRoads().from_bbox(bbox_value, additionnal_nodes)

    @staticmethod
    def roads_from_osmgt_file(osmgt_file_name):
        return OsmGtRoads().from_osmgt_file(osmgt_file_name)

    @staticmethod
    def poi_from_location(location_name):
        return OsmGtPoi().from_location(location_name)

    @staticmethod
    def poi_from_bbox(bbox_value):
        return OsmGtPoi().from_bbox(bbox_value)

    @staticmethod
    def poi_from_osmgt_file(osmgt_file_name):
        return OsmGtPoi().from_osmgt_file(osmgt_file_name)

