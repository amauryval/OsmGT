from osmgt.apis.core import ApiCore


class ErrorOverpassApi(ValueError):
    pass


class OverpassApi(ApiCore):

    __OVERPASS_URL = "https://www.overpass-api.de/api/interpreter"
    __OVERPASS_QUERY_PREFIX = "[out:json];"
    # __OVERPASS_QUERY_SUFFIX = ";(._;>;);out geom;"
    __OVERPASS_QUERY_SUFFIX = ""

    def __init__(self, logger):
        super().__init__()
        self.logger = logger

    def _build_parameters(self, query):
        return {
            "data": f"{self.__OVERPASS_QUERY_PREFIX}{query}{self.__OVERPASS_QUERY_SUFFIX}"
        }

    def query(self, query):
        parameters = self._build_parameters(query)
        return self.compute_query(self.__OVERPASS_URL, parameters)
