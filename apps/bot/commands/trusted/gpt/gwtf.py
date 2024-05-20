from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.commands.trusted.gpt.gemini import Gemini
from apps.bot.commands.trusted.gpt.wtf import WTF


class GWTF(WTF):
    name = "gwtf"

    DEFAULT_PROMPT = "Я пришлю тебе переписку участников группы. Суммаризируй её, опиши, что произошло, о чём общались люди?"

    help_text = HelpText(
        commands_text="обрабатывает сообщения в конфе через Gemini",
        help_texts=[
            HelpTextItem(
                Role.TRUSTED, [
                    HelpTextItemCommand(
                        "[prompt] [N=50]",
                        "обрабатывает последние N сообщений в конфе через Gemini по указанному prompt"),
                    HelpTextItemCommand(
                        "(пересланное сообщение)",
                        "обрабатывает последние сообщения до пересланного в конфе через Gemini по указанному prompt")
                ])
        ],
        extra_text=f"prompt по умолчанию:\n{DEFAULT_PROMPT}"

    )

    GPT_COMMAND_CLASS = Gemini
