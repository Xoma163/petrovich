from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem
from apps.bot.utils.DoTheLinuxComand import do_the_linux_command


class Uptime(Command):
    name = 'аптайм'
    names = ["uptime"]
    help_text = "аптайм сервера"
    access = Role.MODERATOR

    def start(self) -> ResponseMessage:
        command = "uptime"
        answer = do_the_linux_command(command)
        return ResponseMessage(ResponseMessageItem(text=answer))
