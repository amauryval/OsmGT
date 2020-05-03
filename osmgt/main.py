# from osmgt.compoments.osm_web_src import OsmGtWebSource
# from osmgt.compoments.osmgt_file_src import OsmgtFileSource

from osmgt.compoments.network import OsmGtNetwork
from osmgt.compoments.poi import OsmGtPoi


class OsmGt:
    @staticmethod
    def network_from_location(location_name, additionnal_nodes):
        return OsmGtNetwork().from_location(location_name, additionnal_nodes)

    @staticmethod
    def network_from_osmgt_file(osmgt_file_name):
        return OsmGtNetwork().from_osmgt_file(osmgt_file_name)

    @staticmethod
    def poi_from_location(location_name):
        return OsmGtPoi().from_location(location_name)

    @staticmethod
    def poi_from_osmgt_file(osmgt_file_name):
        return OsmGtPoi().from_osmgt_file(osmgt_file_name)
