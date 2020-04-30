
from osmgt.compoments.osm_web_src import OsmGtWebSource
from osmgt.compoments.osmgt_file_src import OsmgtFileSource


class OsmGt:

    @staticmethod
    def network_from_location_name(location_name, additionnal_points=None):
        """
        get a numpy array graph from a location name
        """
        osmgt = OsmGtWebSource(
            location_name,
            additionnal_points
        ).get_data_from_osm()
        return osmgt

    @staticmethod
    def network_from_osmgt_file(osmgt_input_file):
        osmgt = OsmgtFileSource(osmgt_input_file).raise_error.get_data_from_osmgt_file()
        return osmgt
