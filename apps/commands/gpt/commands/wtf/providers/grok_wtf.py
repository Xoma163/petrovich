from apps.bot.consts import RoleEnum
from apps.commands.gpt.commands.gpt.providers.grok import GrokCommand
from apps.commands.gpt.commands.wtf.base import WTFCommand
from apps.commands.help_text import HelpText, HelpTextItem


class GWTF(WTFCommand):
    name = "gwtf"
    names = ['гвтф']

    abstract = False
    access = RoleEnum.TRUSTED

    help_text = HelpText(
        commands_text="обрабатывает сообщения в конфе через Grok",
        help_texts=[
            HelpTextItem(
                access,
                WTFCommand.DEFAULT_HELP_TEXT_ITEMS
            )
        ],
        extra_text=f"prompt по умолчанию:\n{WTFCommand.DEFAULT_PROMPT}"
    )

    def __init__(self):
        super().__init__(GrokCommand)
