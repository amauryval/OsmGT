from typing import Dict

from requests_futures import sessions


from osmgt.helpers.misc import retry


class ErrorRequest(ValueError):
    pass


class ApiCore:
    __slots__ = (
        "logger"
    )
    __NB_WORKER: int = 1
    __WORKED_STATUS_CODE: int = 200

    def check_request_response(self, response) -> None:
        python_class_name = self.__class__.__name__
        response_code = response.result().status_code
        response_reason = f"{response_code}:{response.result().reason}"
        response_result_message = (
            f"{python_class_name}: Query {response_reason} "
            f"in {round(response.result().elapsed.total_seconds(), 2)} sec."
        )
        self.logger.info(f"{response_result_message}")

        if response_code != self.__WORKED_STATUS_CODE:
            raise ErrorRequest(
                f"{response_result_message}"
            )

    @retry(ErrorRequest, tries=4, delay=3, backoff=2, logger=None)
    def request_query(self, url: str, parameters: Dict) -> Dict:

        session = sessions.FuturesSession(max_workers=self.__NB_WORKER)
        response = session.get(url, params=parameters)

        self.check_request_response(response)
        return response.result().json()
