from django.core.management import BaseCommand

from apps.birds.CameraHandler import CameraHandler
from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.bots.vk.VkBot import VkBot
from apps.bot.classes.bots.yandex.YandexBot import YandexBot

camera_handler = CameraHandler()


class Command(BaseCommand):

    def __init__(self):
        super().__init__()

        self.vk_bot = VkBot()
        self.tg_bot = TgBot()
        self.ya_bot = YandexBot()
        self.camera_handler = camera_handler

    def handle(self, *args, **kwargs):
        debug = kwargs.get('debug', False)

        self.vk_bot.start()
        self.tg_bot.start()
        print('start')
        if not debug:
            self.ya_bot.start()
            self.tg_bot.update_help_texts()
        # self.camera_handler.start()

    def add_arguments(self, parser):
        parser.add_argument('debug', type=bool, nargs='?', help='debug mode', default=False)
