import logging

import requests
from requests import Response
from requests.exceptions import HTTPError, JSONDecodeError


class APIHandler:
    def __init__(self, log_filter=None):
        self._logger = logging.getLogger('api')
        self.headers = None
        self.log_filter = log_filter

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
        log_data = {"response": response}
        if self.log_filter:
            log_data.update({'log_filter': self.log_filter})
        self._logger.debug(log_data)


class API:
    def __init__(self, *args, **kwargs):
        super(API, self).__init__()
        self.requests = APIHandler(*args, **kwargs)
