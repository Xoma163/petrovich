from apps.bot.api.ocr import OCR
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpTextItem, HelpText, HelpTextItemCommand
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class Text(Command):
    name = "текст"

    help_text = HelpText(
        commands_text="распознаёт текст на изображении",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand("Текст (Изображения/Пересылаемое сообщение с изображением) [язык=rus]",
                                    "распознаёт текст на изображении")
            ])
        ],
        extra_text=(
            'Язык нужно указывать в 3 символа. Пример - "eng", "rus", "fre", "ger" и так далее'
        )
    )

    attachments = [PhotoAttachment]

    def start(self) -> ResponseMessage:
        lang = "rus"
        if self.event.message.args:
            lang = self.event.message.args[0]

        ocr_api = OCR()
        image = self.event.get_all_attachments([PhotoAttachment])[0]
        content = image.download_content(self.event.peer_id)
        answer = ocr_api.recognize(content, lang)
        return ResponseMessage(ResponseMessageItem(text=answer))
