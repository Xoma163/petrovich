from django.core.management import BaseCommand

from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.bots.vk.VkBot import VkBot
from apps.bot.classes.bots.yandex.YandexBot import YandexBot


class Command(BaseCommand):
    def __init__(self):
        super().__init__()

        self.vk_bot = VkBot()
        self.tg_bot = TgBot()
        self.ya_bot = YandexBot()

    def handle(self, *args, **kwargs):
        debug = kwargs.get('debug', False)
        self.vk_bot.start()
        self.tg_bot.start()
        print('start')
        if not debug:
            self.tg_bot.update_help_texts()

    def add_arguments(self, parser):
        parser.add_argument('debug', type=bool, nargs='?', help='debug mode', default=False)
