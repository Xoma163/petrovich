from apps.bot.classes.consts.Consts import Role, Platform
from apps.bot.classes.Command import Command


class Flood(Command):
    name = "флуд"
    help_text = "флудит"
    help_texts = ["(N) - флудит N сообщений"]
    access = Role.ADMIN
    args = 1
    int_args = [0]
    platforms = [Platform.VK, Platform.TG]

    def start(self):
        msg = "ыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыыы"
        count = self.event.message.args[0]
        msgs = [{'msg': msg}] * count
        return msgs
