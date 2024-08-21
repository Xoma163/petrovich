from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextItem, HelpText, HelpTextArgument
from apps.bot.commands.mrazi.nostalgia import Nostalgia


class Flaiva(Nostalgia):
    name = "флейва"

    access = Role.FLAIVA
    help_text = HelpText(
        commands_text="генерирует картинку с сообщениями из конфы флейвы",
        help_texts=[
            HelpTextItem(access, [
                HelpTextArgument(None, "присылает 10 случайных сообщений"),
                HelpTextArgument(
                    "(N,M=10)",
                    "присылает сообщения с позиции N до M. Максимальная разница между N и M - 200"),
                HelpTextArgument("(вложения)", "присылает вложения со скриншота"),
                HelpTextArgument("(фраза)", "ищет фразу по переписке"),
                HelpTextArgument("поиск (фраза) [N=1]", "ищет фразу по переписке. N - номер страницы")
            ])
        ]
    )


    KEY = "flaiva"
    FILE = "secrets/flaiva_chats/flaiva.json"

    FLAIVA_CHAT_PK = 46

    def check_rights(self):
        if not (self.event.is_from_pm or self.event.chat and self.event.chat.pk == self.FLAIVA_CHAT_PK):
            raise PWarning("Команда работает только в ЛС или конфе флейвы")
