from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpText, HelpTextItem
from apps.bot.commands.abstract.wtf_command import WTFCommand
from apps.bot.commands.gpt.claude import Claude


class GWTF(WTFCommand):
    name = "cwtf"
    names = ["свтф", "квтф", "цвтф"]

    abstract = False
    access = Role.GPT

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

    def __init__(self, ):
        super().__init__(Claude)
