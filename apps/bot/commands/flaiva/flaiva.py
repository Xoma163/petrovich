from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.commands.mrazi.nostalgia import Nostalgia


class Flaiva(Nostalgia):
    name = "флейва"
    help_text = "генерирует картинку с сообщениями из конфы флейвы"

    access = Role.FLAIVA

    KEY = "flaiva"
    FILE = "secrets/flaiva_chats/flaiva.json"

    def check_rights(self):
        if not (self.event.is_from_pm or self.event.chat and self.event.chat.pk == 46):
            raise PWarning("Команда работает только в ЛС или конфе флейвы")
