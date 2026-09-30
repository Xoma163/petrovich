import base64
import binascii
import re
from io import BytesIO

from PIL import Image, UnidentifiedImageError

from apps.bot.consts import RoleEnum
from apps.bot.core.messages.attachments.photo import PhotoAttachment
from apps.bot.core.messages.response_message import ResponseMessageItem
from apps.commands.gpt.commands_utils.gpt.functionality.completions import GPTCompletionsFunctionality
from apps.commands.gpt.commands_utils.gpt.functionality.vision import GPTVisionFunctionality
from apps.commands.gpt.commands_utils.gpt.gpt_abstract import GPTCommand
from apps.commands.gpt.providers.providers.hermes import HermesProvider
from apps.commands.help_text import HelpTextItem, HelpText
from petrovich.settings import env


class HermesCommand(GPTCommand, GPTCompletionsFunctionality, GPTVisionFunctionality):
    INLINE_IMAGE = re.compile(
        r"!\[[^\]\n]*\]\(data:image/(?P<format>png|jpeg|webp|gif);base64,(?P<data>[A-Za-z0-9+/=]+)\)",
        re.IGNORECASE,
    )
    MAX_IMAGE_BYTES = 5 * 1024 * 1024
    MAX_IMAGES = 10

    name = "hermes"
    names = ["гермес"]
    access = RoleEnum.ADMIN
    abstract = False

    provider: HermesProvider = HermesProvider()

    help_text = HelpText(
        commands_text="чат с Hermes Agent",
        help_texts=[
            HelpTextItem(
                access,
                GPTCompletionsFunctionality.COMPLETIONS_HELP_TEXT_ITEMS
                + GPTVisionFunctionality.VISION_HELP_TEXT_ITEMS,
            ),
        ],
        extra_text=GPTCommand.EXTRA_TEXT,
    )

    def get_api_key(self) -> str:
        return env.str("HERMES_API_KEY", default="")

    def get_completions_rmi(self, answer: str) -> ResponseMessageItem:
        images = []

        def extract_image(match: re.Match) -> str:
            if len(images) >= self.MAX_IMAGES:
                return "[Слишком много изображений]"
            encoded = match.group("data")
            if len(encoded) > (self.MAX_IMAGE_BYTES + 2) // 3 * 4:
                return "[Изображение слишком большое]"
            try:
                image_bytes = base64.b64decode(encoded, validate=True)
                if not image_bytes or len(image_bytes) > self.MAX_IMAGE_BYTES:
                    return "[Изображение слишком большое]"
                with Image.open(BytesIO(image_bytes)) as image:
                    image.verify()
                    if image.format.lower() != match.group("format").lower():
                        return "[Некорректное изображение]"
                if match.group("format").lower() in ("gif", "webp"):
                    with Image.open(BytesIO(image_bytes)) as image:
                        output = BytesIO()
                        image.convert("RGB").save(output, format="JPEG", quality=90)
                        image_bytes = output.getvalue()
                    extension = "jpg"
                else:
                    extension = "jpg" if match.group("format").lower() == "jpeg" else "png"
                if len(image_bytes) > self.MAX_IMAGE_BYTES:
                    return "[Изображение слишком большое]"
            except (binascii.Error, OSError, UnidentifiedImageError, ValueError):
                return "[Не удалось прочитать изображение]"

            attachment = PhotoAttachment()
            attachment.parse(_bytes=image_bytes, filename=f"hermes-{len(images) + 1}.{extension}")
            images.append(attachment)
            return ""

        text = self.INLINE_IMAGE.sub(extract_image, answer).strip()
        if not images:
            return super().get_completions_rmi(text)

        return ResponseMessageItem(
            text=text,
            attachments=images,
            reply_to=self.event.message.id,
            peer_id=self.event.peer_id,
            message_thread_id=self.event.message_thread_id,
        )
