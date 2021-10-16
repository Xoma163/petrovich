import threading
import time

import requests

from apps.bot.classes.Consts import Platform
from apps.bot.classes2.bots.Bot import Bot
from apps.bot.classes2.events.TgEvent import TgEvent
from apps.bot.classes2.messages.ResponseMessageItem import ResponseMessageItem
from petrovich.settings import env

API_TELEGRAM_URL = 'api.telegram.org'


class TgBot(Bot):
    API_TELEGRAM_URL = API_TELEGRAM_URL

    def __init__(self):
        Bot.__init__(self, Platform.TG)

        self.token = env.str("TG_TOKEN")
        self.requests = TgRequests(self.token)
        self.longpoll = MyTgBotLongPoll(self.token, self.requests)

    def listen(self):
        """
        Получение новых событий и их обработка
        """
        for raw_event in self.longpoll.listen():
            tg_event = TgEvent(raw_event)
            threading.Thread(target=self.handle_event, args=(tg_event,)).start()

    def send_message(self, rm: ResponseMessageItem):
        """
        Отправка сообщения
        """
        prepared_message = {'chat_id': rm.peer_id, 'text': rm.text, 'parse_mode': 'HTML', 'reply_markup': rm.keyboard}
        return self.requests.get('sendMessage', params=prepared_message)


class TgRequests:
    def __init__(self, token):
        self.token = token

    def get(self, method_name, params=None, **kwargs):
        url = f'https://{API_TELEGRAM_URL}/bot{self.token}/{method_name}'
        return requests.get(url, params, **kwargs)

    def post(self, method_name, params=None, **kwargs):
        url = f'https://{API_TELEGRAM_URL}/bot{self.token}/{method_name}'
        return requests.post(url, params, **kwargs)


class MyTgBotLongPoll:
    def __init__(self, token, request=None):
        self.token = token
        if request is None:
            self.request = TgRequests(token)
        else:
            self.request = request

        self.last_update_id = 1
        self._get_last_update_id()

    def _get_last_update_id(self):
        """
        Запоминание последнего обработанного собщения
        """
        result = self.request.get('getUpdates')
        if result.status_code == 200:
            result = result.json()['result']
            if len(result) > 0:
                self.last_update_id = result[-1]['update_id'] + 1

    def check(self):
        """
        Проверка на новое сообщение
        """
        result = self.request.get('getUpdates', {'offset': self.last_update_id, 'timeout': 30}, timeout=35)
        if result.status_code != 200:
            return []
        result = result.json()['result']
        return result

    def listen(self):
        while True:
            try:
                for event in self.check():
                    yield event
                    self.last_update_id = event['update_id'] + 1
                time.sleep(0.5)

            except Exception as e:
                error = {'exception': f'Longpoll Error (TG): {str(e)}'}
                print(error)
