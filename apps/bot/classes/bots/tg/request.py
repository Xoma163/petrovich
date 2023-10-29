import logging

import requests
from requests import Response

from apps.bot.utils.cache import MessagesCache


class Request:
    API_TELEGRAM_URL = 'api.telegram.org'
    PREFIX = "https"

    LOG_IGNORE_ACTIONS = ['sendChatAction']

    def __init__(self, token):
        self.token = token
        self.logger = logging.getLogger('bot')

    def get(self, action, params=None, **kwargs) -> Response:
        return self._do(action, "post", params, **kwargs)

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
        level = "debug" if response['ok'] else "error"
        getattr(self.logger, level)({"response": response, "action": action})

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
