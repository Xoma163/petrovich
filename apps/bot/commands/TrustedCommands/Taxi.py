from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand
from petrovich.settings import STATIC_DIR


class Taxi(CommonCommand):
    names = ["такси"]
    help_text = "Такси - график отношения цены ко времени"
    access = Role.TRUSTED

    def start(self):
        attachments = self.bot.upload_photos(f"{STATIC_DIR}/bot/img/taxi.png")
        return {'attachments': attachments}
