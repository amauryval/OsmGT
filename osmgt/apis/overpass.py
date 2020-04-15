import geopandas as gpd

from shapely.geometry import Point
from shapely.geometry import LineString
from shapely.geometry import Polygon
import geojson
import numpy as np

from osmgt.apis.core import ApiCore
from osmgt.network.graphtools_helper import GraphHelpers


class ErrorOverpassApi(ValueError):
    pass


class OverpassApi(ApiCore):

    __OVERPASS_URL = "https://www.overpass-api.de/api/interpreter"
    __OVERPASS_QUERY_PREFIX = "[out:json];"
    # __OVERPASS_QUERY_SUFFIX = ";(._;>;);out geom;"
    __OVERPASS_QUERY_SUFFIX = ""
    __EPSG = 4326

    def __init__(self, query):
        super().__init__()

        self._query = query
        parameters = self._build_parameters()
        self._result_query = self.compute_query(self.__OVERPASS_URL, parameters)
        self.__format_data()

        self._output = []

    def _build_parameters(self):
        return {"data": f"{self.__OVERPASS_QUERY_PREFIX}{self._query}{self.__OVERPASS_QUERY_SUFFIX}"}

    def __format_data(self):
        self._raw_data = self._result_query["elements"]

    def to_linestrings(self):
        ways_found = filter(lambda feature: feature["type"] == "way", self._raw_data)

        self._output = [
            geojson.Feature(
                geometry=LineString(map(lambda x: (x["lon"], x["lat"]), feature["geometry"])),
                properties=self.__get_tags(feature)
            )
            for feature in ways_found
            if "geometry" in feature
        ]
        return self.__to_gdf()

    def to_numpy_array(self):
        ways_found = filter(lambda feature: feature["type"] == "way", self._raw_data)
        for feature in ways_found:

            coordinates = list(map(lambda x: (x["lon"], x["lat"]), feature["geometry"]))
            for nodes in zip(coordinates, coordinates[1:]):
                data = {}
                data.update(self.__get_tags(feature))
                data["node_1"] = nodes[0]
                data["node_2"] = nodes[-1]
                data["length"] = LineString(nodes).length
                array = np.array(data)

                self._output.append(array)

        return self.__to_numpy_array()

    def to_polygons(self):
        ways_found = filter(lambda feature: feature["type"] in ("way", "relation"), self._raw_data)
        for feature in ways_found:
            if "geometry" in feature and len(feature["geometry"]) > 2:
                geometry = geojson.Feature(
                    geometry=Polygon(
                        [
                            (geom["lon"], geom["lat"])
                            for geom in feature["geometry"]
                        ]
                    ),
                    properties=self.__get_tags(feature)
                )
                self._output.append(geometry)

            elif "members" in feature:
                inners = filter(lambda x: x["role"] == "inner", feature["members"])
                outer = list(filter(lambda x: x["role"] == "outer", feature["members"]))[0]

                if "geometry" in outer:
                    inners = [
                        [
                            (item["lon"], item["lat"])
                            for item in inner["geometry"]
                        ]
                        for inner in inners
                        if "geometry" in inner
                    ]

                    geometry = geojson.Feature(
                        geometry=Polygon(
                            [
                                (item["lon"], item["lat"])
                                for item in outer["geometry"]
                            ],
                            inners
                        ),
                        properties=self.__get_tags(feature)
                    )
                    self._output.append(geometry)

        return self.__to_gdf()

    def to_points(self):
        nodes_found = filter(lambda feature: feature["type"] == "node", self._raw_data)

        self._output = [
            geojson.Feature(
                geometry=Point(feature["lon"], feature["lat"]),
                properties=self.__get_tags(feature)
            )
            for feature in nodes_found
        ]
        return self.__to_gdf()

    def __to_gdf(self):
        self.__check_formated_data()

        output = gpd.GeoDataFrame.from_features(self._output)
        output.crs = self.__EPSG
        output = output.to_crs(3857)
        return output

    def __to_numpy_array(self):
        self.__check_formated_data()
        output = np.stack(self._output)
        return output

    def to_graph(self):
        self.to_numpy_array()
        graph = GraphHelpers(directed=False)

        for feature in self._output:
            feature_dict = feature.tolist()
            graph.add_edge(
                str(feature_dict["node_1"]),
                str(feature_dict["node_2"]),
                f'{str(feature_dict["node_1"])}_{str(feature_dict["node_2"])}',
                feature_dict["length"],
            )
        return graph

    def __get_tags(self, feature):
        return feature.get("tags", {})

    def __check_formated_data(self):
        if len(self._output) == 0:
            raise ErrorOverpassApi("Data empty")
