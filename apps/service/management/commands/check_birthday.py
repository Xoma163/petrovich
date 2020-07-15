from datetime import datetime

from django.core.management.base import BaseCommand

from apps.bot.classes.bots.VkBot import VkBot
from apps.bot.models import Chat, Users
from apps.games.models import Gamer

vk_bot = VkBot()


class Command(BaseCommand):

    def handle(self, *args, **options):
        chat_ids = options['chat_id'][0].split(',')
        for chat_id in chat_ids:
            chat = Chat.objects.filter(chat_id=vk_bot.get_group_id(chat_id)).first()

            if not chat:
                print(f"Чата с id = {chat_id} не существует")
                break

            today = datetime.now()
            users = Users.objects.filter(chats=chat,
                                         birthday__day=today.day,
                                         birthday__month=today.month)

            for user in users:
                vk_bot.send_message(chat.chat_id, f"С Днём рождения, {vk_bot.get_mention(user)}!")

                gamer = Gamer.objects.filter(user=user).first()
                if gamer:
                    gamer.roulette_points += 10000
                    gamer.save()
                    vk_bot.send_message(chat.chat_id, f"На ваш счет зачислено 10 000 бонусных очков.")

    def add_arguments(self, parser):
        parser.add_argument('chat_id', nargs='+', type=str,
                            help='chat_id')
