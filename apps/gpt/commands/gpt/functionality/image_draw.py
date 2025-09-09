from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextArgument, HelpTextKey
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.gpt.api.base import GPTAPI
from apps.gpt.api.responses import GPTImageDrawResponse
from apps.gpt.enums import GPTImageFormat, GPTImageQuality
from apps.gpt.models import ImageDrawModel, ImageEditModel
from apps.gpt.protocols import GPTCommandProtocol, HasImageDraw


class GPTImageDrawFunctionality(GPTCommandProtocol):
    IMAGE_DRAW_HELP_TEXT_ITEMS = [
        HelpTextArgument(
            "нарисуй (фраза/пересланное сообщение)",
            "генерация изображения"
        )
    ]

    IMAGE_EDIT_HELP_TEXT_ITEMS = [
        HelpTextArgument(
            "фотошоп (фраза) [изображение]",
            "редактирование и генерация изображения"
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
        "нарисуй пришлёт несколько изображений. Максимум 10"
    )
    KEY_ITEM_HD = HelpTextKey(
        "hd",
        ['xd', 'hq', 'хд'],
        "нарисуй пришлёт изображения в высоком качестве"
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

    EXTRA_TEXT = (
        "По умолчанию для генерации изображения выбирается модель с качеством Standard и квадратным разрешением"
    )

    # MENU

    def menu_image_draw(self) -> ResponseMessageItem:
        return self.image_draw()

    # def menu_image_edit(self) -> ResponseMessageItem:
    #     """
    #     Редактирование изображения
    #     """
    #     self.attachments = [PhotoAttachment]
    #     self.check_attachments()
    #
    #     return self._image_edit()

    # HANDLERS

    def image_draw(self):
        """
        Генерация изображения
        """
        gpt_api: GPTAPI | HasImageDraw = self.provider.api_class(
            api_key=self.get_api_key(),
            log_filter=self.event.log_filter
        )
        request_text = self._get_draw_image_request_text()
        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_PHOTO, self.event.peer_id):
            response: GPTImageDrawResponse = gpt_api.draw_image(
                prompt=request_text,
                model=self.get_image_draw_model_with_parameters(),
                count=self._get_images_count_by_keys()
            )

            self.add_statistics(api_response=response)

            attachments = []
            for i, image in enumerate(response.images_bytes):
                if self._get_use_original_image():
                    att = self.bot.get_document_attachment(
                        image,
                        send_chat_action=False,
                        filename=f'{self.provider.name}_draw_{i + 1}.png'
                    )
                    att.download_content()
                    att.set_thumbnail(att.content)
                else:
                    att = self.bot.get_photo_attachment(image, send_chat_action=False)
                    att.download_content()
                attachments.append(att)

        image_prompt = response.images_prompt if response.images_prompt else request_text
        answer = f'Результат генерации по запросу "{image_prompt}"'

        profile_settings = self.get_profile_gpt_settings()
        if profile_settings.use_debug:
            answer += self.get_debug_text(response)

        return ResponseMessageItem(text=answer, attachments=attachments, reply_to=self.event.message.id)

    # def _image_edit(self):
    #     request_text = self._get_draw_image_request_text()
    #     count = self._get_images_count_by_keys()
    #     use_document_att = self.event.message.is_key_provided({"orig", "original", "ориг", "оригинал"})
    #
    #     gpt_api = self.provider.api_class(log_filter=self.event.log_filter, sender=self.event.sender)
    #     with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_PHOTO, self.event.peer_id):
    #         image = self.event.get_all_attachments([PhotoAttachment])[0]
    #         cropped_image_bytes_png = crop_image_to_square(convert_jpg_to_png(image.download_content()))
    #         side = min(image.width, image.height)
    #         mask_bytes = get_transparent_rgba_png(side, side)
    #
    #         response: GPTImageDrawResponse = gpt_api.edit_image(
    #             request_text,
    #             cropped_image_bytes_png,
    #             mask_bytes,
    #             count=count
    #         )
    #
    #         self.add_statistics(api_response=response)
    #
    #         attachments = []
    #         for i, image in enumerate(response.images_bytes):
    #             if use_document_att:
    #                 att = self.bot.get_document_attachment(
    #                     image,
    #                     send_chat_action=False,
    #                     filename=f'gpt_draw_{i + 1}.png'
    #                 )
    #                 att.download_content()
    #                 att.set_thumbnail(att.content)
    #             else:
    #                 att = self.bot.get_photo_attachment(image, send_chat_action=False)
    #                 att.download_content()
    #                 attachments.append(att)
    #
    #     image_prompt = response.images_prompt if response.images_prompt else request_text
    #     answer = f'Результат редактирования изображения по запросу "{image_prompt}"'
    #     return ResponseMessageItem(text=answer, attachments=attachments, reply_to=self.event.message.id)

    # COMMON UTILS

    def get_image_draw_model_with_parameters(self) -> ImageDrawModel:
        current_image_model = self.get_image_draw_model()

        image_quality = self._get_image_quality() or current_image_model.image_quality
        image_format = self._get_image_format() or current_image_model.image_format

        image_draw_models = ImageDrawModel.objects.filter(
            provider=self.provider_model,
            name=current_image_model.name
        )

        available_models = [
            model for model in image_draw_models
            if model.image_quality == image_quality and \
               model.image_format == image_format
        ]

        if len(available_models) == 0:
            raise PWarning(
                "Не смог определить какую модель с какими характеристиками нужно использовать. Проверьте ваш запрос и доступные модели"
            )
        if len(available_models) > 1:
            raise PWarning(
                "Не смог определить какую модель с какими характеристиками нужно использовать. Подходит сразу несколько. Сообщите админу"
            )
        return available_models[0]

    def get_image_draw_model(self) -> ImageDrawModel:
        return self.get_model(ImageDrawModel, "image_draw_model")

    def get_default_image_draw_model(self) -> ImageDrawModel:
        return self.get_default_model(ImageDrawModel)

    def get_image_edit_model(self) -> ImageEditModel:
        return self.get_model(ImageEditModel, "image_edit_model")

    def get_default_image_edit_model(self) -> ImageEditModel:
        return self.get_default_model(ImageEditModel)

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
        Получение формата изображения, которую хочет получить пользователь.

        По умолчанию SQUARE
        """
        if self.event.message.is_key_provided({'square', 'квадрат', 'квадратная', 'квадратную'}):
            return GPTImageFormat.SQUARE
        elif self.event.message.is_key_provided({'album', 'альбом', 'альбомная', 'альбомную'}):
            return GPTImageFormat.LANDSCAPE
        elif self.event.message.is_key_provided({'portair', 'портрет', 'портретная', 'портретную'}):
            return GPTImageFormat.PORTAIR
        return None

    def _get_image_quality(self) -> GPTImageQuality | None:
        """
        Получение качества изображения, которую хочет получить пользователь.

        По умолчанию MEDIUM
        """

        if self.event.message.is_key_provided({"hd", "xd", "hq", "хд"}):
            return GPTImageQuality.HIGH
        return None

    def _get_images_count_by_keys(self) -> int:
        """
        Определение числа изображений, которое хочет сгенерировать пользователь
        """

        count = 1
        if keys := self.event.message.keys:
            for key in keys:
                if key.isdigit():
                    count = int(key)
                    break
        MAX_IMAGES_COUNT = 10
        if count > MAX_IMAGES_COUNT:
            raise PWarning(f"Максимальное число изображений в запросе - {MAX_IMAGES_COUNT}")
        return count

    def _get_use_original_image(self) -> bool:
        """
        Получение информации, хочет ли пользователь получить изображение в оригинале или нет
        """
        return self.event.message.is_key_provided({"orig", "original", "ориг", "оригинал"})
