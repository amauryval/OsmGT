import requests
from osmgt.apis.core import ApiCore

class ErrorNominatimApi(ValueError):
    pass


class NominatimApi(ApiCore):

    nominatim_url = "https://nominatim.openstreetmap.org/search/?"

    query_parameter = "q"
    other_query_parameter = {"street", "city", "county", "state", "country", "postalcode"}

    format_parameter = {"format": "json"}

    _output = []

    def __init__(self, **params):
        super().__init__()

        parameters = self.__check_parameters(params)
        self.__RESULT_QUERY = self.compute_query(self.nominatim_url, parameters)

    def __check_parameters(self, input):
        parameters = {}

        if self.query_parameter in input:
            # clean arguments set
            for param_key in self.other_query_parameter:
                try:
                    del input[param_key]
                except KeyError:
                    pass

        elif not any([input_key in self.other_query_parameter for input_key in input.keys()]):
            raise ErrorNominatimApi(f"{', '.join(self.other_query_parameter)} not found!")

        parameters.update(input)
        parameters.update(self.format_parameter)

        return parameters

    def data(self):
        return self.__RESULT_QUERY
