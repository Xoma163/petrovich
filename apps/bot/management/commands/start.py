from django.core.management import BaseCommand

from apps.birds.CameraHandler import CameraHandler
from apps.bot.classes.bots.TgBot import TgBot
from apps.bot.classes.bots.VkBot import VkBot

vk_bot = VkBot()
tg_bot = TgBot()
camera_handler = CameraHandler()


def start_camera():
    camera_handler.start()
    print('start camera')


class Command(BaseCommand):

    def __init__(self):
        super().__init__()

    def handle(self, *args, **kwargs):
        debug = kwargs.get('debug', False)

        vk_bot.start()
        tg_bot.start()
        print('start')
        if not debug:
            tg_bot.update_help_texts()
            start_camera()

    def add_arguments(self, parser):
        parser.add_argument('debug', type=bool, nargs='?', help='debug mode', default=False)
