import logging

import requests
from requests import Response
from requests.exceptions import HTTPError, JSONDecodeError


class APIHandler:
    def __init__(self):
        self._logger = logging.getLogger('api')
        self.headers = None

    def get(self, url, *args, **kwargs) -> Response:
        return self._do(url, "get", *args, **kwargs)

    def post(self, url, *args, **kwargs) -> Response:
        return self._do(url, "post", *args, **kwargs)

    def _do(self, url, method, *args, **kwargs) -> Response:
        log = kwargs.pop('log', True)
        if not kwargs.get('headers') and self.headers:
            kwargs['headers'] = self.headers

        r: Response = getattr(requests, method)(url, *args, **kwargs)

        if not log:
            return r

        try:
            r.raise_for_status()
            r_json = r.json()
            self._log(r_json)
        except (HTTPError, JSONDecodeError):
            self._log(r.text)
        return r

    def _log(self, response):
        self._logger.debug({"response": response})


class API:
    def __init__(self):
        self.requests = APIHandler()
