from apps.bot.classes.Consts import Role
from apps.bot.classes.DoTheLinuxComand import do_the_linux_command
from apps.bot.classes.common.CommonCommand import CommonCommand


class Uptime(CommonCommand):
    def __init__(self):
        names = ["аптайм", "uptime"]
        help_text = "Аптайм - аптайм сервера"
        super().__init__(names, help_text, access=Role.MODERATOR)

    def start(self):
        command = "uptime"
        result = do_the_linux_command(command)
        return result
