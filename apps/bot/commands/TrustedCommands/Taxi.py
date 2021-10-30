from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from petrovich.settings import STATIC_ROOT


class Taxi(Command):
    name = "такси"
    help_text = "график отношения цены ко времени"
    access = Role.TRUSTED

    def start(self):
        return {'attachments': self.bot.upload_photos(f"{STATIC_ROOT}/bot/img/taxi.png", peer_id=self.event.peer_id)}
