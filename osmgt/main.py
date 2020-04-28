import os

from osmgt.main_core import MainCore


class OsmGt(MainCore):

    def __init__(self, location_name, new_points):
        """
        get a road data from a location name

        :param location_name: the location name
        :type location_name: str
        """
        super().__init__(logger_name="OsmGt", location_name=location_name, new_points=new_points)

        self._location_name = location_name

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

        return self.to_numpy_array()

    def get_road_gdf_from_location(self, export_to_file=False):
        """
        get a geodataframe from a location name

        :param export_to_file: to export or not a file
        :type export_to_file: bool, default False
        """
        output_gdf = self.to_linestrings()
        if export_to_file:
            output_file = os.path.join(os.getcwd(), "network_output_data.shp")
            self.logger.info(f"Exporting to {output_file}...")
            # output_gdf.to_file(output_file, layer=f"{self._location_name}_roads", driver='GPKG')
            output_gdf.to_file(output_file, driver='ESRI Shapefile')

        return output_gdf
