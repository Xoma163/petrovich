from apps.bot.consts import RoleEnum
from apps.commands.gpt.commands.chatgpt import ChatGPTCommand
from apps.commands.gpt.commands_utils.wtf.wtf_abstract import WTFCommand
from apps.commands.help_text import HelpText, HelpTextItem


class WTF(WTFCommand):
    name = "wtf"
    names = ['втф', 'саммари', 'суммаризируй']

    abstract = False
    access = RoleEnum.TRUSTED

    help_text = HelpText(
        commands_text="обрабатывает сообщения в конфе через ChatGPT",
        help_texts=[
            HelpTextItem(
                access,
                WTFCommand.DEFAULT_HELP_TEXT_ITEMS
            )
        ],
        extra_text=f"prompt по умолчанию:\n{WTFCommand.DEFAULT_PROMPT}"
    )

    def __init__(self):
        super().__init__(ChatGPTCommand)
