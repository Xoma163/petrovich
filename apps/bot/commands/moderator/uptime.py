from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.do_the_linux_command import do_the_linux_command


class Uptime(Command):
    name = 'аптайм'
    names = ["uptime"]
    help_text = "аптайм сервера"
    access = Role.MODERATOR

    def start(self) -> ResponseMessage:
        command = "uptime"
        answer = do_the_linux_command(command)
        return ResponseMessage(ResponseMessageItem(text=answer))
