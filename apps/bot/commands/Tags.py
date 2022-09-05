from apps.bot.classes.Command import Command
from apps.bot.commands.Tag import Tag


class Tags(Command):
    name = "теги"
    help_text = "список тегов в конфе"
    conversation = True

    def start(self):
        self.event.message.parse_raw("тег список")
        return Tag(self.bot, self.event).start()
