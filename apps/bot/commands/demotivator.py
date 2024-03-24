import io

from PIL import Image

from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.attachments.sticker import StickerAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.demotivator import DemotivatorBuilder


class Demotivator(Command):
    name = "демотиватор"

    help_text = HelpText(
        commands_text="создаёт демотиватор",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand(
                    "(Изображения/Пересылаемое сообщение с изображением) (большой текст)[\nмаленький текст]",
                    "создаёт демотиватор")
            ])
        ],
        extra_text=(
            "Разделитель текста - перенос строки"
        )
    )

    args = 1
    attachments = [PhotoAttachment, StickerAttachment]

    def start(self) -> ResponseMessage:
        image = self.event.get_all_attachments(self.attachments)[0]
        if isinstance(image, StickerAttachment) and image.animated:
            raise PWarning("Пришлите стикер без анимации")

        text = self.event.message.raw.split(' ', 1)[1]

        texts = list(map(str.strip, text.split('\n', 1)))
        if not texts[0]:
            raise PWarning("Первая фраза обязательно должна быть")

        base_image = Image.open(image.get_bytes_io_content(self.event.peer_id))
        db = DemotivatorBuilder(base_image, *texts)
        demotivator = db.get_demotivator()
        img_byte_arr = io.BytesIO()
        demotivator.save(img_byte_arr, format="PNG")

        attachment = self.bot.get_photo_attachment(
            img_byte_arr,
            peer_id=self.event.peer_id,
            filename="petrovich_demotivator.png"
        )
        return ResponseMessage(ResponseMessageItem(attachments=[attachment]))
