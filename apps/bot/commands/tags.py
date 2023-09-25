from apps.bot.classes.command import Command
from apps.bot.classes.messages.response_message import ResponseMessage
from apps.bot.commands.tag import Tag


class Tags(Command):
    name = "теги"
    help_text = "список тегов в конфе"
    conversation = True

    def start(self) -> ResponseMessage:
        self.event.message.parse_raw("тег список")
        return Tag(self.bot, self.event).start()
