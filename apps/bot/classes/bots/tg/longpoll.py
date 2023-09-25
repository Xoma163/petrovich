import time

from apps.bot.classes.bots.tg.request import Request


class TgBotLongPoll:
    def __init__(self, token):
        self.token = token
        self.request = Request(token)
        self.last_update_id = None

    def set_last_update_id(self):
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
