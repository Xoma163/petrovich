import logging

import requests
from requests import Response

from apps.bot.utils.cache import MessagesCache


class Request:
    API_TELEGRAM_URL = 'api.telegram.org'
    PREFIX = "https"

    LOG_IGNORE_ACTIONS = []

    LOG_WARNING_ERRORS = [
        "Forbidden: bot was blocked by the user",
        "Bad Request: message to edit not found",
        "Bad Request: message can't be deleted",
        "Bad Request: message can't be deleted for everyone"
    ]

    def __init__(self, token, log_filter=None):
        self.token = token
        self.logger = logging.getLogger('bot')
        self.log_filter = log_filter

    def get(self, action, params=None, **kwargs) -> Response:
        return self._do(action, "get", params, **kwargs)

    def post(self, action, params=None, **kwargs) -> Response:
        return self._do(action, "post", params, **kwargs)

    def _do(self, action, method="get", params=None, **kwargs) -> Response:
        url = f'{self.PREFIX}://{self.API_TELEGRAM_URL}/bot{self.token}/{action}'
        r = getattr(requests, method)(url, params, **kwargs)
        r_json = r.json()
        self._log(r_json, action)
        self._cache(r_json)
        return r

    def _log(self, response: dict, action):
        if action in self.LOG_IGNORE_ACTIONS:
            return

        if response['ok']:
            level = "debug"
        elif response['description'] in self.LOG_WARNING_ERRORS:
            level = "warning"
        else:
            level = "error"

        log_data = {"response": response, "action": action}
        if self.log_filter:
            log_data.update({'log_filter': self.log_filter})
        getattr(self.logger, level)(log_data)

    @staticmethod
    def _cache(response: dict):
        if not response['ok']:
            return

        message = response['result']
        if not isinstance(message, dict):
            return
        if 'chat' not in message:
            return
        peer_id = message['chat']['id']
        message_id = message['message_id']

        mc = MessagesCache(peer_id)
        mc.add_message(message_id, message)


class RequestLocal(Request):
    API_TELEGRAM_URL = '192.168.1.10:10010'
    PREFIX = "http"
