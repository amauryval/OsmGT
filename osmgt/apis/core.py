from requests_futures import sessions


class ErrorRequest(ValueError):
    pass


class ApiCore:

    def check_request_response(self, response):
        python_class_name = self.__class__.__name__
        response_code = response.result().status_code
        response_reason = f"{response_code}:{response.result().reason}"
        response_result_message = f"{python_class_name}: Query {response_reason} in {response.result().elapsed.total_seconds()} sec."

        if response_code == 200:
            self.logger.info(
                f"{response_result_message}"
            )
        else:
            raise ErrorRequest(
                f"{response_result_message} ; url={response.result().url}"
            )


    def request_query(self, url, parameters):

        session = sessions.FuturesSession(max_workers=1)
        response = session.get(url, params=parameters)

        self.check_request_response(response)
        return response.result().json()

