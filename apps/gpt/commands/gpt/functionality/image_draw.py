from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextArgument, HelpTextKey
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.gpt.api.responses import GPTImageDrawResponse
from apps.gpt.commands.gpt.protocols import HasCommandFields
from apps.gpt.enums import GPTImageFormat, GPTImageQuality
from apps.gpt.models import Usage


class ImageDrawFunctionality(HasCommandFields):
    DRAW_HELP_TEXT_ITEMS = [
        HelpTextArgument(
            "нарисуй (фраза/пересланное сообщение)",
            "генерация картинки"
        )
    ]

    KEY_ITEM_ORIG = HelpTextKey(
        "orig",
        ["original", "ориг", "оригинал"],
        "нарисуй пришлёт документ без сжатия, а не картинку"
    )
    KEY_ITEM_COUNT = HelpTextKey(
        "(число)",
        [],
        "нарисуй пришлёт несколько картинок. Максимум 10"
    )
    KEY_ITEM_HD = HelpTextKey(
        "hd",
        ['xd', 'hq', 'хд'],
        "нарисуй пришлёт картинки в высоком качестве"
    )
    KEY_ITEMS_FORMAT = [
        HelpTextKey(
            "квадрат",
            ['квадратная', 'square'],
            "нарисуй пришлёт квадратную картинку"
        ),
        HelpTextKey(
            "альбом",
            ['альбомная', 'album'],
            "нарисуй пришлёт альбомную картинку"
        ),
        HelpTextKey(
            "портрет",
            ['портретная', 'portair'],
            "нарисуй пришлёт портретную картинку"
        )
    ]

    # MENU
    def menu_image_draw(self, use_statistics=True) -> ResponseMessageItem:
        """
        Рисование изображения
        """
        request_text = self._get_draw_image_request_text()
        image_format = self._get_image_format()
        gpt_api = self.provider.api_class(log_filter=self.event.log_filter, sender=self.event.sender)
        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_PHOTO, self.event.peer_id):
            count = self._get_images_count_by_keys()

            quality: GPTImageQuality = GPTImageQuality.STANDARD
            if self.event.message.is_key_provided({"hd", "xd", "hq", "хд"}):
                quality = GPTImageQuality.HIGH

            response: GPTImageDrawResponse = gpt_api.image_draw(request_text, image_format, quality, count=count)
            if use_statistics:
                Usage.add_statistics(self.event.sender, response.usage, provider=self.provider)

            use_document_att = self.event.message.is_key_provided({"orig", "original", "ориг", "оригинал"})

            attachments = []
            if use_document_att:
                for i, image in enumerate(response.get_images()):
                    att = self.bot.get_document_attachment(
                        image,
                        send_chat_action=False,
                        filename=f'gpt_draw_{i + 1}.png'
                    )
                    att.download_content()
                    att.set_thumbnail(att.content)
                    attachments.append(att)
            else:
                for image in response.get_images():
                    att = self.bot.get_photo_attachment(image, send_chat_action=False)
                    att.download_content()
                    attachments.append(att)
        image_prompt = response.images_prompt if response.images_prompt else request_text
        answer = f'Результат генерации по запросу "{image_prompt}"'
        return ResponseMessageItem(text=answer, attachments=attachments, reply_to=self.event.message.id)

    def _get_draw_image_request_text(self) -> str:
        """
        Получение текста, который хочет нарисовать пользователь
        """

        if len(self.event.message.args) > 1:
            msg_args = self.event.message.args_case[1:]
            text = " ".join(msg_args)
            return text
        elif self.event.message.quote:
            return self.event.message.quote
        elif self.event.fwd:
            return self.event.fwd[0].message.raw
        else:
            raise PWarning("Должен быть текст или пересланное сообщение")

    def _get_image_format(self) -> GPTImageFormat | None:
        """
        Получение формата картинки, которую хочет получить пользователь.
        """
        if self.event.message.is_key_provided({'square', 'квадрат', 'квадратная'}):
            return GPTImageFormat.SQUARE
        elif self.event.message.is_key_provided({'album', 'альбом', 'альбомная'}):
            return GPTImageFormat.ALBUM
        elif self.event.message.is_key_provided({'portair', 'портрет', 'портретная'}):
            return GPTImageFormat.PORTAIR
        return GPTImageFormat.SQUARE

    def _get_images_count_by_keys(self) -> int:
        count = 1
        if keys := self.event.message.keys:
            for key in keys:
                if key.isdigit():
                    count = int(key)
                    break
        MAX_IMAGES_COUNT = 10
        if count > MAX_IMAGES_COUNT:
            raise PWarning(f"Максимальное число картинок в запросе - {MAX_IMAGES_COUNT}")
        return count
