import json
import re

from apps.bot.classes.Consts import Platform
from petrovich.settings import env


def auto_str(cls):
    def __str__(self):
        items_str = ', '.join('%s=%s' % item for item in vars(self).items())
        return f"{type(self).__name__}({items_str}"

    cls.__str__ = __str__
    return cls


@auto_str
class Event:

    @staticmethod
    def delete_slash_and_mentions(msg):
        """
        Удаление слеша перед началом команды и всех оповещений бота
        """
        mentions = env.list('VK_BOT_MENTIONS')

        # Обрезаем палку
        if len(msg) > 0:
            if msg[0] == '/':
                msg = msg[1:]
            for mention in mentions:
                msg = msg.replace(mention, '')
        return msg

    @staticmethod
    def parse_msg(msg):
        # Сообщение, команда, аргументы, аргументы строкой, ключи
        """
        Парсинг сообщения на разные части

        msg - оригинальное сообщение
        clear_msg - сообщение без лишних пробелов, запятых и с заменённой ё на е
        command - команда
        args - список аргументов
        original_args - строка аргументов (без ключей)
        params - оригинальное сообщение без команды (с аргументами и ключами)

        """
        clear_msg = re.sub(" +", " ", msg)
        clear_msg = re.sub(",+", ",", clear_msg)
        clear_msg = clear_msg.strip().strip(',').strip().strip(' ').strip().replace('ё', 'е').replace('Ё', 'Е')

        msg_dict = {
            'msg': msg,
            'clear_msg': clear_msg,
            'command': None,
            'args': None,
            'original_args': None,
        }

        command_arg = clear_msg.split(' ', 1)
        msg_dict['command'] = command_arg[0].lower()
        if len(command_arg) > 1:
            if len(command_arg[1]) > 0:
                msg_dict['args'] = command_arg[1].split(' ')
                msg_dict['original_args'] = command_arg[1].strip()

        return msg_dict

    def parse_attachments(self, attachments):
        """
        Распаршивание вложений
        """
        raise NotImplementedError

    def __init__(self, event):
        """
        Преобразование собранных данных с ботов
        """
        if 'message' in event:
            raw_msg = event['message'].get('text')
            self.msg_id = event['message'].get('id')
            text = self.delete_slash_and_mentions(raw_msg)
            self.mentioned = raw_msg != text
            parsed = self.parse_msg(text)
            self.msg = parsed.get('msg')
            self.clear_msg = parsed.get('clear_msg')
            self.command = parsed.get('command')
            self.args = parsed.get('args')
            self.original_args = parsed.get('original_args')

            self.attachments = self.parse_attachments(event['message'].get('attachments'))
            self.action = event['message'].get('action')

            self.payload = None
            if 'payload' in event['message'] and event['message']['payload']:
                self.payload = json.loads(event['message']['payload'])
                self.msg = None
                self.command = self.payload['command']
                self.args = None
                self.original_args = None
                if 'args' in self.payload:
                    if isinstance(self.payload['args'], dict):
                        self.args = [arg for arg in self.payload['args'].values()]
                    elif isinstance(self.payload['args'], list):
                        self.args = self.payload['args']
                    else:
                        self.args = [self.payload['args']]
                    self.original_args = " ".join([str(arg) for arg in self.args])

        self.sender = event.get('sender')
        self.chat = event.get('chat')
        self.peer_id = event.get('peer_id')

        if self.chat:
            self.from_chat = True
            self.from_user = False
        else:
            self.from_user = True
            self.from_chat = False

        self.fwd = event.get('fwd', None)

        self.platform = event.get('platform', None)

        self.yandex = event.get('yandex', None)


def get_event_by_platform(platform):
    from apps.bot.classes.events.TgEvent import TgEvent
    from apps.bot.classes.events.VkEvent import VkEvent
    platforms = {
        Platform.VK: VkEvent,
        Platform.TG: TgEvent
    }
    return platforms[platform]
