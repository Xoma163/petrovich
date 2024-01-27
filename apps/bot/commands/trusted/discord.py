from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpText
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage


class Discord(Command):
    name = "дискорд"
    names = ["диск"]

    help_text = HelpText(
        commands_text="ссылка на канал в дискорде"
    )

    access = Role.TRUSTED

    def start(self) -> ResponseMessage:
        url = 'https://discord.gg/kYGSNzv'
        answer = self.bot.get_formatted_url("Дискорд", url)
        return ResponseMessage(ResponseMessageItem(text=answer))
