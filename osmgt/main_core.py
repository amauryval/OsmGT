from osmgt.apis.nominatim import NominatimApi
from osmgt.apis.overpass import OverpassApi


import geopandas as gpd

from shapely.geometry import Point

import geojson

from osmgt.common.osmgt_core import OsmGtCore

# from osmgt.network.graphtools_helper import GraphHelpers
from osmgt.geometry.reprojection import ogr_reproject

from shapely.geometry import LineString

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
        raw_data_restructured = self.__prepare_network_to_be_cleaned()
        self._output = GeomNetworkCleaner(self.logger, raw_data_restructured, new_points).run()

    def __get_data_from_osm(self):
        location_id = NominatimApi(self.logger, q=self._location_name, limit=1).data()[0]["osm_id"]
        location_id += self.__LOCATION_OSM_DEFAULT_ID
        raw_data = OverpassApi(self.logger, location_osm_id=location_id).data()["elements"]
        self._raw_data = filter(lambda x: x["type"] == "way", raw_data)

    def __prepare_network_to_be_cleaned(self):
        self.logger.info(f"Prepare Data")

        raw_data_reprojected = []
        for feature in self._raw_data:
            try:
                feature["geometry"] = ogr_reproject(
                    LineString([(coords["lon"], coords["lat"]) for coords in feature["geometry"]]),
                    self.epsg_4236, self.epsg_3857
                )

            except:
                feature["geometry"] = LineString([(coords["lon"], coords["lat"]) for coords in feature["geometry"]])
            feature["bounds"] = feature["geometry"].bounds
            feature["geometry"] = feature["geometry"].coords[:]

            raw_data_reprojected.append(feature)

        return raw_data_reprojected

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
