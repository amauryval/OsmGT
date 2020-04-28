from osmgt.apis.nominatim import NominatimApi
from osmgt.apis.overpass import OverpassApi


import geopandas as gpd

from shapely.geometry import Point

import geojson

from osmgt.common.osmgt_core import OsmGtCore

# from osmgt.network.graphtools_helper import GraphHelpers
from osmgt.geometry.reprojection import ogr_reproject


from osmgt.geometry.geom_network_cleaner import GeomNetworkCleaner


class OsmGtCoreError(ValueError):
    pass


class MainCore(OsmGtCore):

    __NUMBER_OF_NODES_INTERSECTIONS = 2
    __NEXT_INDEX = 1
    __ITEM_LIST_SEPARATOR = "_"
    __GRAPH_FIELDS = {"node_1", "node_2", "geometry", "length"}
    __ID_FIELD = "uuid"

    __INPUT_EPSG = 4326
    __OUTPUT_EPSG = 3857
    __LOCATION_OSM_DEFAULT_ID = 3600000000  # this is it...

    _ways_to_add = []

    def __init__(self, logger_name, location_name, new_points):
        super().__init__(logger_name=logger_name)
        self.logger.info(f"========== OSMGT ==========")
        self.logger.info(f"Working location: {location_name}")

        self._location_name = location_name
        self._new_points = new_points

        self._output = []
        self.__get_data_from_osm()

        # data processing
        self.__prepare_network_to_be_cleaned()
        self._output = GeomNetworkCleaner(self.logger, self._raw_data_filtered_restructured, new_points).run()

    def __get_data_from_osm(self):
        location_id = NominatimApi(self.logger, q=self._location_name, limit=1).data()[0]["osm_id"]
        location_id += self.__LOCATION_OSM_DEFAULT_ID
        self._raw_data = OverpassApi(self.logger, location_osm_id=location_id).data()["elements"]

    def __prepare_network_to_be_cleaned(self):
        self.logger.info(f"Prepare Data")

        # TODO reproject here
        # geometry = ogr_reproject(LineString(line_coordinates), self.__INPUT_EPSG, self.__OUTPUT_EPSG)

        # TODO prepare a generic format, in parallel of source data
        raw_data_filtered = filter(lambda x: x["type"] == "way", self._raw_data)
        raw_data_filtered_restructured = {}
        for feature in raw_data_filtered:
            raw_data_filtered_restructured[str(feature["id"])] = feature
            raw_data_filtered_restructured[str(feature["id"])]["geometry"] = [
                [coords["lon"] for coords in feature["geometry"]],
                [coords["lat"] for coords in feature["geometry"]]
            ]
        self._raw_data_filtered_restructured = raw_data_filtered_restructured

    def to_numpy_array(self):
        return self._output

    def to_linestrings(self):
        features = []
        for feature in self._output:
            geometry = feature["geometry"]
            properties = {
                key: feature[key] for key in feature.keys()
                if key not in self.__GRAPH_FIELDS
            }
            feature = geojson.Feature(
                geometry=geometry,
                properties=properties
            )
            features.append(feature)

        return self.__to_gdf(features)

    def to_points(self):
        nodes_found = filter(lambda feature: feature["type"] == "node", self._raw_data)

        features = [
            geojson.Feature(
                geometry=Point(feature["lon"], feature["lat"]),
                properties=self._get_tags(feature)
            )
            for feature in nodes_found
        ]
        return self.__to_gdf(features)

    def __to_gdf(self, features):
        self.logger.info(f"Prepare Geodataframe")
        output = gpd.GeoDataFrame.from_features(features)
        output.crs = self.epsg_4236
        # output = output.to_crs(self.epsg_3857)
        return output

    # def to_graph(self):
    #     self.to_numpy_array()
    #     graph = GraphHelpers(directed=False)
    #
    #     for feature in self._output:
    #         graph.add_edge(
    #             str(feature["node_1"]),
    #             str(feature["node_2"]),
    #             feature["id"],
    #             feature["length"],
    #         )
    #     return graph

    def _get_tags(self, feature):
        return feature.get("tags", {})
