import re

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.models import Chat
from apps.bot.utils.cache import MessagesCache


class Command(BaseCommand):

    def handle(self, *args, **options):
        ids = [
            "35270409",
            "86878496",
            "202938014",
            "241805142",
            "8129898",
        ]
        chat_pk = options['chat_id'][0]
        chat: Chat = Chat.objects.get(pk=chat_pk)

        ratings = []
        for _id in ids:
            r = requests.get(f"https://app.scope.gg/dashboard/{_id}")
            bs4 = BeautifulSoup(r.content, 'html.parser')
            data = bs4.find("div", {'class': re.compile('^PremierRatingIcon__RankWrapper')})
            if not data:
                continue
            rating = int(data.text)
            ratings.append(rating)
        mmr = int(sum(ratings) / len(ratings))

        tg_bot = TgBot()
        chat_title = tg_bot.get_chat(chat.chat_id)['result']['title']

        r = re.compile(r'\| (\d{4,}) MMR')

        if existed_mmr := r.finditer(chat_title):
            match = list(existed_mmr)[0]
            chat_mmr = chat_title[match.regs[1][0]:match.regs[1][1]]
            if chat_mmr == str(mmr):
                return
            new_chat_title = chat_title[:match.regs[1][0]] + str(mmr) + chat_title[match.regs[1][1]:]
        else:
            new_chat_title = f"{chat_title} | {mmr} MMR"

        message_id = tg_bot._send_text({'chat_id': chat.chat_id, 'caption': 'test'})['result']['message_id']
        tg_bot.delete_message(chat.chat_id, message_id)
        mc = MessagesCache(int(chat.chat_id))
        data = mc.get_messages()
        tg_bot.set_chat_title(chat.chat_id, new_chat_title)
        if message_id + 1 not in data:
            tg_bot.delete_message(chat.chat_id, message_id + 1)

    def add_arguments(self, parser):
        parser.add_argument('chat_id', nargs='+', type=str, help='chat_id')
