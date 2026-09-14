from apps.bot.core.chat_action_sender import ChatActionSender
from apps.bot.core.chat_actions import ChatActionEnum
from apps.bot.core.messages.response_message import ResponseMessageItem
from apps.commands.gpt.api.base import GPTAPI
from apps.commands.gpt.api.responses import GPTImageDrawResponse
from apps.commands.gpt.enums import GPTImageFormat, GPTImageQuality
from apps.commands.gpt.models import ImageDrawModel
from apps.commands.gpt.protocols import GPTCommandProtocol, HasImageDraw
from apps.commands.help_text import HelpTextArgument, HelpTextKey
from apps.shared.exceptions import PWarning


class GPTImageDrawFunctionality(GPTCommandProtocol):
    IMAGE_DRAW_HELP_TEXT_ITEMS = [HelpTextArgument("нарисуй (фраза/пересланное сообщение)", "генерация изображения")]

    KEY_ITEM_ORIG = HelpTextKey(
        "orig", ["original", "ориг", "оригинал"], "нарисуй пришлёт документ без сжатия, а не картинку"
    )
    KEY_ITEM_COUNT = HelpTextKey("(число)", [], "нарисуй пришлёт несколько изображений. Максимум 10")
    KEY_ITEMS_QUALITY = [
        HelpTextKey("low", ["низкое"], "низкое качество"),
        HelpTextKey("medium", ["среднее"], "среднее качество"),
        HelpTextKey("high", ["hd", "xd", "hq", "хд", "высокое"], "высокое качество"),
        HelpTextKey("xhigh", ["xhd", "очень-высокое"], "очень высокое качество"),
        HelpTextKey("max", ["максимальное"], "максимальное качество"),
    ]
    KEY_ITEMS_FORMAT = [
        HelpTextKey("квадрат", ["квадратная", "square"], "нарисуй пришлёт квадратную картинку"),
        HelpTextKey("альбом", ["альбомная", "album"], "нарисуй пришлёт альбомную картинку"),
        HelpTextKey("портрет", ["портретная", "portair"], "нарисуй пришлёт портретную картинку"),
    ]

    EXTRA_TEXT = (
        "Качество и размер по умолчанию задаются выбранной моделью. Их можно изменить ключами команды"
    )

    # MENU

    def menu_image_draw(self) -> ResponseMessageItem:
        return self.image_draw()

    # HANDLERS

    def image_draw(self):
        """
        Генерация изображения
        """
        gpt_api: GPTAPI | HasImageDraw = self.provider.api_class(
            api_key=self.get_api_key(), log_filter=self.event.log_filter
        )
        request_text = self._get_draw_image_request_text()
        with ChatActionSender(self.bot, ChatActionEnum.UPLOAD_PHOTO, self.event.peer_id, self.event.message_thread_id):
            response: GPTImageDrawResponse = gpt_api.draw_image(
                prompt=request_text,
                model=self.get_image_draw_model_with_parameters(),
                count=self._get_images_count_by_keys(),
            )

            self.add_statistics(api_response=response)

            attachments = []
            for i, image in enumerate(response.images_bytes):
                if self._get_use_original_image():
                    att = self.bot.get_document_attachment(
                        _bytes=image,
                        thumbnail_bytes=image,
                        send_chat_action=False,
                        filename=f"{self.provider.type_enum.name}_draw_{i + 1}.png",
                    )
                    att.download_content()
                else:
                    att = self.bot.get_photo_attachment(_bytes=image, send_chat_action=False)
                    att.download_content()
                attachments.append(att)

        image_prompt = response.images_prompt if response.images_prompt else request_text
        answer = f'Результат генерации по запросу "{image_prompt}"'

        profile_settings = self.get_profile_gpt_settings()
        if profile_settings.use_debug:
            answer += self.get_debug_text(response)

        return ResponseMessageItem(text=answer, attachments=attachments, reply_to=self.event.message.id)

    # COMMON UTILS

    def get_image_draw_model_with_parameters(self) -> ImageDrawModel:
        current_image_model = self.get_image_draw_model()

        image_quality = self._get_image_quality() or current_image_model.image_quality
        image_format = self._get_image_format() or current_image_model.image_format
        if image_quality is None:
            raise PWarning(
                f'У модели "{current_image_model.name}" некорректно настроено качество по умолчанию'
            )

        quality = image_quality.value
        supported_qualities = current_image_model.supported_qualities or [current_image_model.quality]
        if quality not in supported_qualities:
            raise PWarning(
                f'Модель "{current_image_model.name}" не поддерживает качество "{quality}"'
            )

        supported_sizes = current_image_model.supported_sizes or [current_image_model.size]
        available_sizes = [size for size in supported_sizes if self._get_size_format(size) == image_format]
        if not available_sizes:
            raise PWarning(f'Модель "{current_image_model.name}" не поддерживает выбранный формат изображения')

        width, height = map(int, available_sizes[0].split("x", maxsplit=1))
        current_image_model.width = width
        current_image_model.height = height
        current_image_model.quality = quality
        return current_image_model

    @staticmethod
    def _get_size_format(size: str) -> GPTImageFormat:
        width, height = map(int, size.split("x", maxsplit=1))
        if width > height:
            return GPTImageFormat.LANDSCAPE
        if width < height:
            return GPTImageFormat.PORTAIR
        return GPTImageFormat.SQUARE

    def get_image_draw_model(self) -> ImageDrawModel:
        return self.get_model(ImageDrawModel, "image_draw_model")

    def get_default_image_draw_model(self) -> ImageDrawModel:
        return self.get_default_model(ImageDrawModel)

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
        if self.event.message.is_key_provided({"square", "квадрат", "квадратная", "квадратную"}):
            return GPTImageFormat.SQUARE
        elif self.event.message.is_key_provided({"album", "альбом", "альбомная", "альбомную"}):
            return GPTImageFormat.LANDSCAPE
        elif self.event.message.is_key_provided({"portair", "портрет", "портретная", "портретную"}):
            return GPTImageFormat.PORTAIR
        return None

    def _get_image_quality(self) -> GPTImageQuality | None:
        """
        Получение качества изображения, которую хочет получить пользователь.

        По умолчанию MEDIUM
        """

        if self.event.message.is_key_provided({"max", "максимальное"}):
            return GPTImageQuality.MAX
        if self.event.message.is_key_provided({"xhigh", "xhd", "очень-высокое"}):
            return GPTImageQuality.XHIGH
        if self.event.message.is_key_provided({"high", "hd", "xd", "hq", "хд", "высокое"}):
            return GPTImageQuality.HIGH
        if self.event.message.is_key_provided({"medium", "среднее"}):
            return GPTImageQuality.MEDIUM
        if self.event.message.is_key_provided({"low", "низкое"}):
            return GPTImageQuality.LOW
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
        if count < 1:
            raise PWarning("Минимальное число изображений в запросе - 1")
        if count > MAX_IMAGES_COUNT:
            raise PWarning(f"Максимальное число изображений в запросе - {MAX_IMAGES_COUNT}")
        return count

    def _get_use_original_image(self) -> bool:
        """
        Получение информации, хочет ли пользователь получить изображение в оригинале или нет
        """
        return self.event.message.is_key_provided({"orig", "original", "ориг", "оригинал"})
