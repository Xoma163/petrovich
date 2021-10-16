from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.Command import Command
from apps.service.management.commands.get_words import Command


class Words(Command):
    name = "слова"
    help_text = "принудительно затягивает слова с Google Drive"
    access = Role.MODERATOR

    def start(self):
        get_words = Command()
        return get_words.handle()
