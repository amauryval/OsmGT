from osmgt.core import OsmGtCore


class OsmGt:

    def __init__(self, location_name, new_points):
        """
        get a road data from a location name

        :param location_name: the location name
        :type location_name: str
        """

        self._location_name = location_name
        self._osm_result = OsmGtCore(location_name, new_points)

    # def get_graph_from_location(self):
    #     """
    #     get a graph tool graph from a location name
    #
    #     """
    #
    #     return self._osm_result.to_graph()

    def get_road_numpy_array_from_location(self):
        """
        get a numpy array graph from a location name
        """

        return self._osm_result.to_numpy_array()

    def get_road_gdf_from_location(self, export_to_file=False):
        """
        get a geodataframe from a location name

        :param export_to_file: to export or not a file
        :type export_to_file: bool, default False
        """

        if export_to_file:
            self._osm_result.to_linestrings().to_file(f"{self._location_name}_roads.geojson", driver='GeoJSON')

        return self._osm_result.to_linestrings()
