import json
import re

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
    def delete_slash_and_mentions(msg, mentions):
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
        msg - оригинальное сообщение
        command - команда
        args - список аргументов
        original_args - строка аргументов (без ключей)
        params - оригинальное сообщение без команды (с аргументами и ключами)

        """
        msg_clear = re.sub(" +", " ", msg)
        msg_clear = re.sub(",+", ",", msg_clear)
        msg_clear = msg_clear.strip().strip(',').strip().strip(' ').strip().replace('ё', 'е')

        msg_dict = {'msg': msg,
                    'msg_clear': msg_clear,
                    'command': None,
                    'args': None,
                    'original_args': None,
                    }

        command_arg = msg_clear.split(' ', 1)
        msg_dict['command'] = command_arg[0].lower()
        if len(command_arg) > 1:
            if len(command_arg[1]) > 0:
                msg_dict['args'] = command_arg[1].split(' ')
                msg_dict['original_args'] = command_arg[1].strip()

        return msg_dict

    def parse_attachments(self, attachments):
        raise NotImplementedError

    def __init__(self, event):
        mentions = env.list('VK_BOT_MENTIONS')
        if 'message' in event:
            text = self.delete_slash_and_mentions(event['message'].get('text'), mentions)
            parsed = self.parse_msg(text)
            self.msg = parsed.get('msg')
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
        'vk': VkEvent,
        'tg': TgEvent
    }
    return platforms[platform]
