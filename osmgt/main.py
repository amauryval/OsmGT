import os

from osmgt.main_core import MainCore


class OsmGt(MainCore):

    def __init__(self, location_name=None, additionnal_points=None, numpy_file_path=None):
        """
        get a road data from a location name

        :param location_name: the location name
        :type location_name: str
        """
        super().__init__(
            logger_name="OsmGt",
            location_name=location_name,
            additionnal_points=additionnal_points,
            numpy_file_path=numpy_file_path
        )

    # def get_graph_from_location(self):
    #     """
    #     get a graph tool graph from a location name
    #
    #     """
    #     self.logger.info("Prepare graph...")
    #     return self.to_graph()

    def get_road_numpy_array_from_location(self):
        """
        get a numpy array graph from a location name
        """

        return self._output

    def get_road_gdf_from_location(self, export_to_file=False):
        """
        get a geodataframe

        :param export_to_file: to export or not a file
        :type export_to_file: bool, default False
        """
        output_gdf = self.to_gdf(export_to_file)

        if not export_to_file:
            return output_gdf
