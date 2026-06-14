import re

from apps.bot.consts import RoleEnum
from apps.bot.core.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.commands.command import Command
from apps.commands.help_text import HelpText, HelpTextArgument, HelpTextItem


class Markdown(Command):
    name = "markdown"
    names = ["md"]
    args = 1

    help_text = HelpText(
        commands_text="присылает форматированный текст",
        help_texts=[
            HelpTextItem(
                RoleEnum.USER,
                [HelpTextArgument("(текст)", "прислать текст с форматированием markdown")],
            ),
        ],
    )

    def start(self) -> ResponseMessage:
        text = self.get_raw_markdown_text()
        rmi = ResponseMessageItem(text=text)
        rmi.set_rich_markdown()
        return ResponseMessage(rmi)

    def get_raw_markdown_text(self) -> str:
        raw = self.event.message.raw.lstrip()
        if raw.startswith("/"):
            raw = raw[1:]

        msg_split = re.split(self.event.message.SPACE_REGEX, raw, 1)
        if len(msg_split) == 1:
            return self.event.message.args_str_case
        return msg_split[1]
