from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextItem, HelpText
from apps.bot.commands.mrazi.nostalgia import Nostalgia


class Flaiva(Nostalgia):
    name = "флейва"

    help_text = HelpText(
        commands_text="генерирует картинку с сообщениями из конфы флейвы",
        help_texts=[
            HelpTextItem(Role.FLAIVA, [
                "- присылает 10 случайных сообщений",
                "(N,M=10) - присылает сообщения с позиции N до M. Максимальная разница между N и M - 200",
                "(вложения) - присылает вложения со скриншота",
                "(фраза) - ищет фразу по переписке",
                "поиск (фраза) [N=1] - ищет фразу по переписке. N - номер страницы"
            ])
        ]
    )

    access = Role.FLAIVA

    KEY = "flaiva"
    FILE = "secrets/flaiva_chats/flaiva.json"

    def check_rights(self):
        if not (self.event.is_from_pm or self.event.chat and self.event.chat.pk == 46):
            raise PWarning("Команда работает только в ЛС или конфе флейвы")
