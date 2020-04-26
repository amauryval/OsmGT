import requests


class ErrorRequestResponse(ValueError):
    pass


class ApiCore:

    def check_request_response(self, response):
        response_code = response.status_code

        if response_code == 200:
            print(f"Query success ({response_code}) in {str(response.elapsed)} sec.")
        elif response_code == 400:
            raise ErrorRequestResponse(f"Query Bad Query ({response_code}).")
        elif response_code == 404:
            raise ErrorRequestResponse(f"Query bad request ({response_code}).")
        else:
            print(f"response code not implemented yet: {response_code}")

    def compute_query(self, url, parameters):
        response = requests.get(
            url,
            params=parameters
        )

        self.check_request_response(response)
        return response.json()
