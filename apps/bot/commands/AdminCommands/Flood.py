from apps.bot.classes.Consts import Role, Platform
from apps.bot.classes.common.CommonCommand import CommonCommand


class Flood(CommonCommand):
    name = "флуд"
    help_text = "флудит"
    help_texts = ["(N) - флудит N сообщений"]
    access = Role.ADMIN
    args = 1
    int_args = [0]
    platforms = [Platform.VK, Platform.TG]

    def start(self):
        msg = "ыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыы"
        count = self.event.args[0]
        msgs = [{'msg': msg}] * count
        return msgs
