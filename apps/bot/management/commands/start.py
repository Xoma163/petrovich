from django.core.management import BaseCommand

from apps.birds.CameraHandler import CameraHandler
from apps.bot.classes.bots.TgBot import TgBot
from apps.bot.classes.bots.VkBot import VkBot

vk_bot = VkBot()
tg_bot = TgBot()
camera_handler = CameraHandler()


def start_vk(debug=False):
    vk_bot.DEVELOP_DEBUG = debug
    vk_bot.start()
    print('start vk')


def start_tg(debug=False):
    tg_bot.DEVELOP_DEBUG = debug
    tg_bot.start()
    print('start tg')


def start_camera():
    camera_handler.start()
    print('start camera')


class Command(BaseCommand):

    def __init__(self):
        super().__init__()

    def handle(self, *args, **kwargs):
        if 'debug' in kwargs:
            debug = kwargs['debug']
        else:
            debug = False

        start_vk(debug)
        start_tg(debug)
        if not debug:
            start_camera()
