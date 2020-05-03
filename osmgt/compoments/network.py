from osmgt.compoments.core import OsmGtCore

from osmgt.apis.nominatim import NominatimApi
from osmgt.apis.overpass import OverpassApi

from osmgt.geometry.reprojection import ogr_reproject
from osmgt.geometry.geom_network_cleaner import GeomNetworkCleaner

import geojson
from shapely.geometry import LineString

from osmgt.network.gt_helper import GraphHelpers


class ErrorNetworkData(Exception):
    pass


class OsmGtNetwork(OsmGtCore):

    __DATA_NAME = "network"
    _output_data = None

    def __init__(self):
        super().__init__()

    def from_location(self, location_name, additionnal_nodes):
        self.logger.info(f"From location: {location_name}")

        self.logger.info("Loading network data...")
        location_id = NominatimApi(self.logger, q=location_name, limit=1).data()[0]["osm_id"]
        location_id += self.location_osm_default_id
        location_id_query_part = self.__from_location_builder(location_id)

        query = f"{location_id_query_part}{self.__road_query}"
        raw_data = OverpassApi(self.logger).querier(query)["elements"]

        self._output_data = self.__build_network_topology(raw_data, additionnal_nodes)

        return self

    def get_graph(self):
        self.check_build_input_data()
        graph = GraphHelpers()

        for feature in self._output_data:
            graph.add_edge(
                feature["geometry"].coords[0],
                feature["geometry"].coords[-1],
                feature["uuid"],
                feature["geometry"].coords[0].length,
            )
        return graph

    def __build_network_topology(self, raw_data, additionnal_nodes):
        raw_data_restructured = self.__rebuild_network_data(raw_data)
        raw_data_topology_rebuild = GeomNetworkCleaner(
            self.logger,
            raw_data_restructured,
            additionnal_nodes
        ).run()

        return raw_data_topology_rebuild

    def __rebuild_network_data(self, raw_data):
        self.logger.info("Formating data")

        raw_data = filter(lambda x: x["type"] == "way", raw_data)
        features = []
        for uuid_enum, feature in enumerate(raw_data, start=1):
            try:
                geometry = ogr_reproject(
                    LineString([(coords["lon"], coords["lat"]) for coords in feature["geometry"]]),
                    self.epsg_4236, self.epsg_3857
                )
            except:
                geometry = LineString([(coords["lon"], coords["lat"]) for coords in feature["geometry"]])
            del feature["geometry"]

            properties = feature
            del feature["type"]
            properties["bounds"] = ", ".join(map(str, geometry.bounds))
            properties["uuid"] = uuid_enum
            properties = {**properties, **self.insert_tags_field(properties)}
            del properties["tags"]

            feature = geojson.Feature(
                geometry=geometry,
                properties=properties
            )
            features.append(feature)

        return features

    @property
    def __road_query(self):
        query = 'way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|pedestrian|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link|living_street|service|track|bus_guideway|escape|raceway|road|footway|bridleway|steps|corridor|path)$"]["area"!~"."]'
        return '(%s(area.searchArea););out geom;(._;>;);' % query

    def __from_location_builder(self, location_osm_id):
        return f"area({location_osm_id})->.searchArea;"
