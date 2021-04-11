from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.service.management.commands.get_words import Command


class Words(CommonCommand):
    name = "слова"
    help_text = "принудительно затягивает слова с Google Drive"
    access = Role.MODERATOR

    def start(self):
        get_words = Command()
        return get_words.handle()
