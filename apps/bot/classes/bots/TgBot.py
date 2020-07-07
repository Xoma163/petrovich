from threading import Thread

import telebot

from apps.bot.classes.bots.CommonBot import CommonBot
from apps.bot.models import TgUser as TgUserModel, TgChat as TgChatModel, TgBot as TgBotModel
from petrovich.settings import env

bot = telebot.TeleBot(env.str("TG_TOKEN"))


class TgBot(CommonBot, Thread):
    def __init__(self):
        CommonBot.__init__(self)
        Thread.__init__(self)

        self.bot = bot

        self.user_model = TgUserModel
        self.chat_model = TgChatModel
        self.bot_model = TgBotModel

    def run(self):
        self.bot.polling(none_stop=True)

    @staticmethod
    @bot.message_handler(content_types=["text"])
    def listen(message):
        # fucking lib ><
        event = message
        tg_event = {
            'from_user': not event.json['from']['is_bot'],
            'user_id': event.from_user.id,
            'chat_id': None,
            'peer_id': event.json['chat']['id'],
            'message': {
                'id': message.json['message_id'],
                'text': event.json['text'],
                # 'payload': event.message.payload,
                # 'attachments': event.message.attachments,
                # 'action': event.message.action
            },
            'fwd': None
        }
        if not tg_event['from_user']:
            tg_event['chat_id'] = message.json['chat']['id']
        if 'reply_to_message' in event.json:
            tg_event['fwd'] = {
                'id': event.json['reply_to_message']['message_id'],
                'text': event.json['reply_to_message']['text'],
            }
        # Игнорим forward
        if 'forward_from' in event.json:
            return

        bot.send_message(message.chat.id, 'test')

        pass
