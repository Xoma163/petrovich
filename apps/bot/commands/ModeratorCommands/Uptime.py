from apps.bot.classes.consts.Consts import Role
from apps.bot.utils.DoTheLinuxComand import do_the_linux_command
from apps.bot.classes.Command import Command


class Uptime(Command):
    name = 'аптайм'
    names = ["uptime"]
    help_text = "аптайм сервера"
    access = Role.MODERATOR

    def start(self):
        command = "uptime"
        result = do_the_linux_command(command)
        return result
