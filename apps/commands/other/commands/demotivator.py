from apps.bot.consts import RoleEnum
from apps.bot.core.messages.attachments.document import DocumentAttachment
from apps.bot.core.messages.attachments.photo import PhotoAttachment
from apps.bot.core.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.commands.command import Command
from apps.commands.help_text import HelpText, HelpTextArgument, HelpTextItem
from apps.shared.exceptions import PWarning
from apps.shared.utils.demotivator import DemotivatorBuilder


class Demotivator(Command):
    name = "демотиватор"
    names = ["demotivator"]
    access = RoleEnum.USER
    args = 1
    attachments = [PhotoAttachment, DocumentAttachment]

    help_text = HelpText(
        commands_text="делает демотиватор",
        help_texts=[
            HelpTextItem(
                access,
                [
                    HelpTextArgument(
                        "(первая строка)\\n[вторая строка] + картинка",
                        "первая строка - крупный заголовок, вторая - мелкая подпись",
                    )
                ],
            )
        ],
        extra_text=(
            "Текст можно переносить строками.\n"
            "Первая строка обязательна и становится заголовком.\n"
            "Начиная со второй строки формируется подпись."
        ),
    )

    def start(self) -> ResponseMessage:
        title, subtitle = self._get_text_lines()
        image_attachment = self._get_image_attachment()

        result_bytes = DemotivatorBuilder(image_attachment, title=title, subtitle=subtitle).build_bytes()
        result_photo = self.bot.get_photo_attachment(
            _bytes=result_bytes,
            filename="demotivator.jpg",
            peer_id=self.event.peer_id,
            message_thread_id=self.event.message_thread_id,
        )
        return ResponseMessage(ResponseMessageItem(attachments=result_photo))

    def _get_text_lines(self) -> tuple[str, str]:
        text_lines = [line.strip() for line in self.event.message.args_str_case.split("\n") if line.strip()]
        if not text_lines:
            raise PWarning("Нужен текст для демотиватора: первая строка обязательна")
        subtitle = "\n".join(text_lines[1:]) if len(text_lines) > 1 else ""
        return text_lines[0], subtitle

    def _get_image_attachment(self) -> PhotoAttachment | DocumentAttachment:
        attachments = self.event.get_all_attachments([PhotoAttachment, DocumentAttachment])
        for attachment in attachments:
            if isinstance(attachment, PhotoAttachment):
                return attachment
            if isinstance(attachment, DocumentAttachment) and attachment.mime_type and attachment.mime_type.is_image:
                return attachment

        raise PWarning("Подходит только изображение")
