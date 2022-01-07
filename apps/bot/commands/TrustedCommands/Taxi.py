from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.consts.Exceptions import PWarning
from petrovich.settings import STATIC_ROOT


class Taxi(Command):
    name = "такси"
    name_tg = "taxi"

    help_text = "график отношения цены ко времени"
    detail_help_text = [
        "[класс=эконом] график отношения цены ко времени\n"
        "Доступные классы - эконом, комфорт, комфорт+"
    ]
    access = Role.TRUSTED

    def start(self):
        if not self.event.message.args:
            return {'attachments': self.bot.upload_photos(f"{STATIC_ROOT}/bot/img/taxi_econom.png",
                                                          peer_id=self.event.peer_id)}
        else:
            if self.event.message.args[0] in ["э", "эконом"]:
                return {'attachments': self.bot.upload_photos(f"{STATIC_ROOT}/bot/img/taxi_econom.png",
                                                              peer_id=self.event.peer_id)}
            elif self.event.message.args[0] in ["к", "комфорт"]:
                return {'attachments': self.bot.upload_photos(f"{STATIC_ROOT}/bot/img/taxi_comfort.png",
                                                              peer_id=self.event.peer_id)}
            elif self.event.message.args[0] in ["к+", "комфорт+"]:
                return {'attachments': self.bot.upload_photos(f"{STATIC_ROOT}/bot/img/taxi_comfortplus.png",
                                                              peer_id=self.event.peer_id)}
            else:
                raise PWarning("Не знаю такого класса. Доступные: эконом, комфорт, комфорт+")
