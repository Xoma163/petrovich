from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpTextItem, HelpText, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.utils.cache import MessagesCache


class Cache(Command):
    name = "cache"

    access = Role.MODERATOR
    help_text = HelpText(
        commands_text="показывает сколько сообщений в кэше содержится для данного чата",
        help_texts=[
            HelpTextItem(access, [
                HelpTextItemCommand(
                    None,
                    "присылает число, отображающее сколько сообщений в кэше содержится для данного чата"
                )
            ])
        ]
    )

    def start(self):
        mc = MessagesCache(self.event.peer_id)
        answer = str(len(mc.get_messages()))
        return ResponseMessage(ResponseMessageItem(text=answer))
