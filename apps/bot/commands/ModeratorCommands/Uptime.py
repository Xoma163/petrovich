from apps.bot.classes.Consts import Role
from apps.bot.classes.DoTheLinuxComand import do_the_linux_command
from apps.bot.classes.common.CommonCommand import CommonCommand


class Uptime(CommonCommand):
    name = 'аптайм'
    names = ["uptime"]
    help_text = "аптайм сервера"
    access = Role.MODERATOR

    def start(self):
        command = "uptime"
        result = do_the_linux_command(command)
        return result
