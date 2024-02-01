from apps.bot.classes.command import Command
from apps.bot.classes.help_text import HelpText
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from petrovich.settings import STATIC_ROOT


class Donate(Command):
    name = "донат"

    help_text = HelpText(
        commands_text="ссылка на донат",
    )

    URL = 'https://www.donationalerts.com/r/xoma163'

    def start(self) -> ResponseMessage:
        photo = self.bot.get_photo_attachment(
            f"{STATIC_ROOT}/bot/img/donate.jpg",
            peer_id=self.event.peer_id,
            filename="petrovich_donate.jpg"
        )
        answer = self.bot.get_formatted_url("Задонатить", self.URL)
        return ResponseMessage(ResponseMessageItem(text=answer, attachments=[photo]))
