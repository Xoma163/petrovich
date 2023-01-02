from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role


class MessageThreadIdCommand(Command):
    name = "message_thread_id"
    help_text = "Выводит message_thread_id"
    conversation = True
    hidden = True
    suggest_for_similar = False
    access = Role.ADMIN

    def start(self):
        mt_id = self.event.message_thread_id
        if mt_id is None:
            return "Нет message_thread_id"
        return mt_id
