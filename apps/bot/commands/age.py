from apps.bot.api.everypixel import EveryPixel
from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.command import Command
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class Age(Command):
    name = "возраст"

    help_text = HelpText(
        commands_text="оценивает возраст людей на фотографии",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand(
                    "(Изображения/Пересылаемое сообщение с изображением)",
                    "оценивает возраст людей на фотографии")
            ])
        ]
    )

    attachments = [PhotoAttachment]

    def start(self) -> ResponseMessage:
        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_VIDEO, self.event.peer_id):
            att = self.event.get_all_attachments([PhotoAttachment])[0]
            everypixel_api = EveryPixel(log_filter=self.event.log_filter)
            photo: PhotoAttachment = everypixel_api.get_faces_on_photo(att)
        return ResponseMessage(ResponseMessageItem(attachments=[photo]))
