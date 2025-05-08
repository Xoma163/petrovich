from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextArgument, HelpTextKey
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.bot.utils.utils import convert_jpg_to_png, get_transparent_rgba_png, crop_image_to_square
from apps.gpt.api.responses import GPTImageDrawResponse
from apps.gpt.enums import GPTImageFormat, GPTImageQuality
from apps.gpt.protocols import GPTCommandProtocol


class GPTImageDrawFunctionality(GPTCommandProtocol):
    IMAGE_DRAW_HELP_TEXT_ITEMS = [
        HelpTextArgument(
            "нарисуй (фраза/пересланное сообщение)",
            "генерация картинки"
        )
    ]

    IMAGE_EDIT_HELP_TEXT_ITEMS = [
        HelpTextArgument(
            "фотошоп (фраза) [картинка]",
            "редактирование и генерация картинки"
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

    def menu_image_draw(self) -> ResponseMessageItem:
        return self._image_draw()

    def menu_image_edit(self) -> ResponseMessageItem:
        """
        Редактирование изображения
        """
        self.attachments = [PhotoAttachment]
        self.check_attachments()

        return self._image_edit()

    # HANDLERS

    def _image_draw(self):
        """
        Рисование изображения
        """
        request_text = self._get_draw_image_request_text()
        image_format = self._get_image_format()

        count = self._get_images_count_by_keys()

        quality: GPTImageQuality = GPTImageQuality.STANDARD
        if self.event.message.is_key_provided({"hd", "xd", "hq", "хд"}):
            quality = GPTImageQuality.HIGH

        use_document_att = self.event.message.is_key_provided({"orig", "original", "ориг", "оригинал"})

        gpt_api = self.provider.api_class(log_filter=self.event.log_filter, sender=self.event.sender)
        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_PHOTO, self.event.peer_id):
            response: GPTImageDrawResponse = gpt_api.draw_image(request_text, image_format, quality, count=count)

            self.add_statistics(api_response=response)

            attachments = []
            for i, image in enumerate(response.images_bytes):
                if use_document_att:
                    att = self.bot.get_document_attachment(
                        image,
                        send_chat_action=False,
                        filename=f'gpt_draw_{i + 1}.png'
                    )
                    att.download_content()
                    att.set_thumbnail(att.content)
                else:
                    att = self.bot.get_photo_attachment(image, send_chat_action=False)
                    att.download_content()
                attachments.append(att)

        image_prompt = response.images_prompt if response.images_prompt else request_text
        answer = f'Результат генерации по запросу "{image_prompt}"'
        return ResponseMessageItem(text=answer, attachments=attachments, reply_to=self.event.message.id)

    def _image_edit(self):
        request_text = self._get_draw_image_request_text()
        count = self._get_images_count_by_keys()
        use_document_att = self.event.message.is_key_provided({"orig", "original", "ориг", "оригинал"})

        gpt_api = self.provider.api_class(log_filter=self.event.log_filter, sender=self.event.sender)
        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_PHOTO, self.event.peer_id):
            image = self.event.get_all_attachments([PhotoAttachment])[0]
            cropped_image_bytes_png = crop_image_to_square(convert_jpg_to_png(image.download_content()))
            side = min(image.width, image.height)
            mask_bytes = get_transparent_rgba_png(side, side)

            response: GPTImageDrawResponse = gpt_api.edit_image(
                request_text,
                cropped_image_bytes_png,
                mask_bytes,
                count=count
            )

            self.add_statistics(api_response=response)

            attachments = []
            for i, image in enumerate(response.images_bytes):
                if use_document_att:
                    att = self.bot.get_document_attachment(
                        image,
                        send_chat_action=False,
                        filename=f'gpt_draw_{i + 1}.png'
                    )
                    att.download_content()
                    att.set_thumbnail(att.content)
                else:
                    att = self.bot.get_photo_attachment(image, send_chat_action=False)
                    att.download_content()
                    attachments.append(att)

        image_prompt = response.images_prompt if response.images_prompt else request_text
        answer = f'Результат редактирования изображения по запросу "{image_prompt}"'
        return ResponseMessageItem(text=answer, attachments=attachments, reply_to=self.event.message.id)

    # UTILS

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
            return GPTImageFormat.LANDSCAPE
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
