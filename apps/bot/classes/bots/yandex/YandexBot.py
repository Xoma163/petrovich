from apps.bot.classes.bots.Bot import Bot as CommonBot
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.events.YandexEvent import YandexEvent
from apps.bot.classes.messages.ResponseMessage import ResponseMessage


class YandexBot(CommonBot):

    def __init__(self):
        CommonBot.__init__(self, Platform.YANDEX)

    def parse(self, raw_event):
        ya_event = YandexEvent(raw_event, self)
        rm = self.handle_event(ya_event)
        ya_response = self.prepare_yandex_response(rm)
        return ya_response

    @staticmethod
    def prepare_yandex_response(rm: ResponseMessage):
        msg = rm.messages[0]  # Только 1 сообщение
        return {
            "response": {
                "text": msg.text,
                "end_session": True
            },
            "version": "1.0"
        }
