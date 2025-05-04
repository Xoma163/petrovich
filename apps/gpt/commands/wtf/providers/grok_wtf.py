from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpText, HelpTextItem
from apps.gpt.commands.gpt.providers.grok import GrokCommand
from apps.gpt.commands.wtf.base import WTFCommand


class GWTF(WTFCommand):
    name = "gwtf"
    names = ['гвтф']

    abstract = False
    access = Role.GPT

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
