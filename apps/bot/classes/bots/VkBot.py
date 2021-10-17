import json
import threading

import vk_api
from vk_api import VkApi, VkUpload
from vk_api.bot_longpoll import VkBotLongPoll
from vk_api.utils import get_random_id

from apps.bot.classes.bots.Bot import Bot as CommonBot
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.events.VkEvent import VkEvent
from apps.bot.classes.messages.ResponseMessage import ResponseMessageItem, ResponseMessage
from petrovich.settings import env


class VkBot(CommonBot):

    def __init__(self):
        CommonBot.__init__(self, Platform.VK)

        self.token = env.str('VK_BOT_TOKEN')
        self.group_id = env.str('VK_BOT_GROUP_ID')
        vk_session = VkApi(token=self.token, api_version="5.131", config_filename="secrets/vk_bot_config.json")
        self.longpoll = MyVkBotLongPoll(vk_session, group_id=self.group_id)
        self.upload = VkUpload(vk_session)
        self.vk = vk_session.get_api()

    def listen(self):
        """
        Получение новых событий и их обработка
        """
        for raw_event in self.longpoll.listen():
            vk_event = VkEvent(raw_event, self)
            threading.Thread(target=self.handle_event, args=(vk_event,)).start()

    def send_response_message(self, rm: ResponseMessage):
        """
        Отправка ResponseMessage сообщения
        """
        for msg in rm.messages:
            try:
                self.send_message(msg)
            except vk_api.exceptions.ApiError as e:
                if e.code == 901:
                    pass
                error_msg = "Непредвиденная ошибка. Сообщите разработчику. Команда /баг"
                error_rm = ResponseMessage(error_msg, msg.peer_id).messages[0]
                self.logger.error({'result': error_msg, 'error': f"{e.code} {e.error}"})
                self.send_message(error_rm)

    def send_message(self, rm: ResponseMessageItem):
        text = str(rm.text)
        if len(text) > 4096:
            text = text[:4092]
            text += "\n..."
        self.vk.messages.send(peer_id=rm.peer_id,
                              message=text,
                              access_token=self.token,
                              random_id=get_random_id(),
                              attachment=','.join(rm.attachments),
                              keyboard=json.dumps(rm.keyboard),
                              # dont_parse_links=dont_parse_links
                              )


class MyVkBotLongPoll(VkBotLongPoll):
    def listen(self):
        while True:
            try:
                for event in self.check():
                    yield event
            except Exception as e:
                error = {'exception': f'Longpoll Error (VK): {str(e)}'}
                print(error)
