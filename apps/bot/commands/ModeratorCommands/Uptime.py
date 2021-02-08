from apps.bot.classes.Consts import Role
from apps.bot.classes.DoTheLinuxComand import do_the_linux_command
from apps.bot.classes.common.CommonCommand import CommonCommand


class Uptime(CommonCommand):
    names = ["аптайм", "uptime"]
    help_text = "Аптайм - аптайм сервера"
    access = Role.MODERATOR

    def start(self):
        command = "uptime"
        result = do_the_linux_command(command)
        return result
