from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpText, HelpTextItem
from apps.bot.commands.abstract.wtf_command import WTFCommand
from apps.bot.commands.chatgpt import ChatGPT


class WTF(WTFCommand):
    name = "wtf"
    names = ['саммари', 'суммаризируй']

    abstract = False

    access = Role.USER
    chat_gpt_key = True

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

    GPT_COMMAND_CLASS = ChatGPT
