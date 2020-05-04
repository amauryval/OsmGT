import requests


class ErrorRequest(ValueError):
    pass


class ApiCore:

    def check_request_response(self, response):
        python_class_name = self.__class__.__name__
        response_code = response.status_code
        response_reason = f"{response.status_code}:{response.reason}"
        response_elapsed_time = str(response.elapsed)
        response_result_message = f"{python_class_name}: Query {response_reason} in {response_elapsed_time} sec."

        if response_code == 200:
            self.logger.info(
                f"{response_result_message}"
            )
        else:
            raise ErrorRequest(
                f"{response_result_message} ; url={response.url}"
            )


    def compute_query(self, url, parameters):
        response = requests.get(url, params=parameters)

        self.check_request_response(response)
        return response.json()
