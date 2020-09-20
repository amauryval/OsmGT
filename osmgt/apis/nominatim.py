from typing import Dict
from typing import List
from typing import Set

from osmgt.apis.core import ApiCore


class ErrorNominatimApi(ValueError):
    pass


class NominatimApi(ApiCore):

    nominatim_url: str = "https://nominatim.openstreetmap.org/search/?"

    query_parameter: str = "q"
    other_query_parameter: Set[str] = {
        "street",
        "city",
        "county",
        "state",
        "country",
        "postalcode",
    }
    format_parameter: Dict = {"format": "json", "polygon": "1", "polygon_geojson": "1"}

    _output: List = []

    def __init__(self, logger, **params) -> None:
        super().__init__()
        self.logger = logger

        parameters: Dict = self.__check_parameters(params)
        self.__RESULT_QUERY = self.request_query(self.nominatim_url, parameters)

    def __check_parameters(self, input_parameters: Dict) -> Dict:

        if self.query_parameter in input_parameters:
            # clean arguments set
            for param_key in self.other_query_parameter:
                try:
                    del input_parameters[param_key]
                except KeyError:
                    pass

        elif not any(
            [
                input_key in self.other_query_parameter
                for input_key in input_parameters.keys()
            ]
        ):
            raise ErrorNominatimApi(
                f"{', '.join(self.other_query_parameter)} not found!"
            )

        input_parameters.update(self.format_parameter)

        return input_parameters

    def data(self) -> dict:
        return self.__RESULT_QUERY
