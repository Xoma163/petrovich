from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand
from petrovich.settings import STATIC_ROOT


class Taxi(CommonCommand):
    def __init__(self):
        names = ["такси"]
        help_text = "Такси - график отношения цены ко времени"
        super().__init__(names, help_text, access=Role.TRUSTED)

    def start(self):
        attachments = self.bot.upload_photos(f"{STATIC_ROOT}/bot/img/taxi.png")
        return {'attachments': attachments}
