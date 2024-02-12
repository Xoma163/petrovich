from apps.bot.api.bitly import BitLy
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.attachments.link import LinkAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class ShortLinks(Command):
    name = "сс"
    names = ['cc']

    help_text = HelpText(
        commands_text="сокращение ссылки",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand("(ссылка)", "сокращение ссылки"),
                HelpTextItemCommand("(Пересылаемое сообщение)", "сокращение ссылки")
            ])
        ]
    )

    attachments = [LinkAttachment]
    args_or_fwd = True

    def start(self) -> ResponseMessage:
        if self.event.fwd:
            if self.event.message.quote:
                long_link = self.event.message.quote
            else:
                long_link = self.event.fwd[0].attachments[0].url
        else:
            long_link = self.event.attachments[0].url
        try:
            bl_api = BitLy(log_filter=self.event.log_filter)
            answer = bl_api.get_short_link(long_link)
            return ResponseMessage(ResponseMessageItem(text=answer))
        except Exception:
            raise PWarning("Неверный формат ссылки")
