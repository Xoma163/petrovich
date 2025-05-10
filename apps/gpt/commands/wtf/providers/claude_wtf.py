from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpText, HelpTextItem
from apps.gpt.commands.gpt.providers.claude import ClaudeCommand
from apps.gpt.commands.wtf.base import WTFCommand


class CWTF(WTFCommand):
    name = "cwtf"
    names = ["свтф", "квтф", "цвтф"]

    abstract = False
    access = Role.TRUSTED

    help_text = HelpText(
        commands_text="обрабатывает сообщения в конфе через Claude",
        help_texts=[
            HelpTextItem(
                access,
                WTFCommand.DEFAULT_HELP_TEXT_ITEMS
            )
        ],
        extra_text=f"prompt по умолчанию:\n{WTFCommand.DEFAULT_PROMPT}"
    )

    def __init__(self):
        super().__init__(ClaudeCommand)
