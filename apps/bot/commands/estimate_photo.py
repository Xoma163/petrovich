from apps.bot.api.everypixel import EveryPixel
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpTextItem, HelpText, HelpTextItemCommand
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class EstimatePhoto(Command):
    name = "оцени"
    names = ["оценить"]

    help_text = HelpText(
        commands_text="оценить качество фотографии",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand(
                    "(Изображение/Пересылаемое сообщение с изображением)",
                    "оценивает качество изображения")
            ])
        ]
    )

    attachments = [PhotoAttachment]

    def start(self) -> ResponseMessage:
        image = self.event.get_all_attachments([PhotoAttachment])[0]

        everypixel_api = EveryPixel()
        image_bytes = image.download_content(self.event.peer_id)
        image_quality = everypixel_api.get_image_quality(image_bytes)
        answer = f"Качество картинки - {image_quality}"
        return ResponseMessage(ResponseMessageItem(text=answer))
