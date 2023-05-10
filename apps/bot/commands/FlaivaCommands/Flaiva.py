from apps.bot.classes.consts.Consts import Platform, Role
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.commands.MraziCommands.Nostalgia import Nostalgia


class Flaiva(Nostalgia):
    name = "флейва"
    help_text = "генерирует картинку с сообщениями из конфы флейвы"
    help_texts = [
        "- присылает 10 случайных сообщений",
        "(N,M=10) - присылает сообщения с позиции N до M. Максимальная разница между N и M - 200",
        "(до) - присылает несколько сообщений до",
        "(после) - присылает несколыько сообщений после",
        "(вложения) - присылает вложения со скриншота",
        "(фраза) - ищет фразу по переписке",
        "поиск (фраза) [N=1] - ищет фразу по переписке. N - номер страницы"
    ]
    access = Role.FLAIVA

    platforms = [Platform.TG]
    DEFAULT_MSGS_COUNT = 10

    KEY = "flaiva"
    FILE = "secrets/flaiva_chats/flaiva.json"

    def check_rights(self):
        if not (self.event.is_from_pm or self.event.chat and self.event.chat.pk == 46):
            raise PWarning("Команда работает только в ЛС или конфе флейвы")
