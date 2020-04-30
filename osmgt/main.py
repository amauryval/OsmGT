import os

from osmgt.main_core import MainCore


class OsmGt:


    # def get_graph_from_location(self):
    #     """
    #     get a graph tool graph from a location name
    #
    #     """
    #     self.logger.info("Prepare graph...")
    #     return self.to_graph()
    @staticmethod
    def network_from_location_name(location_name, additionnal_points=None):
        """
        get a numpy array graph from a location name
        """
        osmgt = MainCore().get_data_from_osm(
            location_name,
            additionnal_points
        )
        return osmgt

    @staticmethod
    def network_from_osmgt_file(osmgt_input_file):
        osmgt = MainCore().get_data_from_osmgt_file(osmgt_input_file)
        return osmgt
