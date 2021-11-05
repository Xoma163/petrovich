from django.core.management import BaseCommand

from apps.birds.CameraHandler import CameraHandler
from apps.bot.classes.bots.APIBot import APIBot
from apps.bot.initial import COMMANDS

camera_handler = CameraHandler()


class Command(BaseCommand):

    def handle(self, *args, **options):
        api_bot = APIBot()

        commands = COMMANDS
        for command in commands:
            if command.enabled and command.name and command.name.lower() != "рестарт":
                parsed = api_bot.parse({'text': command.name, 'token': "LG26BFHCJZYQN75MQYM9XL683RMGPD"})