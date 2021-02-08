from apps.bot.classes.Consts import Role, Platform
from apps.bot.classes.common.CommonCommand import CommonCommand


class Flood(CommonCommand):
    names = ["флуд"]
    help_text = "Флуд - флудит"
    detail_help_text = "Флуд (N) - флудит N сообщений"
    access = Role.ADMIN
    args = 1
    int_args = [0]
    platforms = [Platform.VK, Platform.TG]

    def start(self):
        msg = "ыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыы"
        count = self.event.args[0]
        msgs = [{'msg': msg}] * count
        return msgs
