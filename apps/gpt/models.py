from django.db import models

from apps.bot.models import Profile, Chat
from apps.bot.utils.fernet import Fernet
from apps.gpt.enums import GPTProviderEnum, GPTImageFormat, GPTImageQuality
from apps.service.mixins import TimeStampModelMixin


class Provider(models.Model):
    name = models.CharField(
        'Провайдер',
        unique=True,
        max_length=32,
        choices=[(provider.value, provider.name) for provider in GPTProviderEnum],  # noqa
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Провайдер"
        verbose_name_plural = "Провайдеры"


class Preprompt(TimeStampModelMixin):
    provider = models.ForeignKey(Provider, models.CASCADE, verbose_name="Провайдер")

    author = models.ForeignKey(Profile, models.CASCADE, verbose_name="Пользователь", null=True, blank=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name="Чат", null=True, blank=True)
    text = models.TextField("Текст препромпта", blank=True)

    def __str__(self):
        return f"{self.author} | {self.chat} | {self.provider}"

    class Meta:
        verbose_name = "Препромпт"
        verbose_name_plural = "Препромпты"
        unique_together = ('author', 'chat', 'provider')


class Usage(TimeStampModelMixin):
    provider = models.ForeignKey(Provider, models.CASCADE, verbose_name="Провайдер")

    author = models.ForeignKey(Profile, models.CASCADE, verbose_name="Пользователь", null=True, db_index=True)
    cost = models.DecimalField("Стоимость запроса", max_digits=10, decimal_places=6)
    model_name = models.CharField("Название модели", blank=True, max_length=256)

    def __str__(self):
        return str(f"{self.author} | {self.provider} | {self.model_name}")

    class Meta:
        verbose_name = "Использование"
        verbose_name_plural = "Использования"


class GPTModel(models.Model):
    provider = models.ForeignKey(Provider, models.CASCADE, verbose_name="Провайдер")

    name = models.CharField(max_length=256, verbose_name="Название модели в API")
    verbose_name = models.CharField(max_length=256, verbose_name="Название модели для пользователя")
    is_default = models.BooleanField(default=False, verbose_name="Модель по умолчанию")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Если модель сохраняется с полем is_default, значит сбрасываем всем остальным поле default
        if self.is_default:
            self.__class__.objects \
                .filter(provider=self.provider, is_default=True) \
                .exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class GPTCompletionsVisionModel(GPTModel):
    prompt_1m_token_cost = models.DecimalField(
        "Стоимость за 1млн. входных токенов",
        max_digits=8,
        decimal_places=4,
    )
    completion_1m_token_cost = models.DecimalField(
        "Стоимость за 1млн. выходных токенов",
        max_digits=8,
        decimal_places=4,
    )

    class Meta:
        abstract = True


class CompletionsModel(GPTCompletionsVisionModel):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'provider'], name='unique_name_completion_model')
        ]

        verbose_name = "Модель обработки текста"
        verbose_name_plural = "Модели обработки текста"


class VisionModel(GPTCompletionsVisionModel):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'provider'], name='unique_name_vision_model')
        ]

        verbose_name = "Модель обработки изображений"
        verbose_name_plural = "Модели обработки изображений"


class GPTImageModel(GPTModel):
    width = models.PositiveSmallIntegerField("Ширина изображения")
    height = models.PositiveSmallIntegerField("Высота изображения")

    @property
    def size(self) -> str:
        return f'{self.width}x{self.height}'

    @property
    def image_format(self) -> GPTImageFormat:
        if self.width > self.height:
            return GPTImageFormat.LANDSCAPE
        elif self.width < self.height:
            return GPTImageFormat.PORTAIR
        return GPTImageFormat.SQUARE

    class Meta:
        abstract = True


class ImageDrawModel(GPTImageModel):
    image_cost = models.DecimalField(
        "Стоимость генерации одного изображения",
        max_digits=8,
        decimal_places=4
    )
    quality = models.CharField("Название качества модели в API", max_length=32)

    @property
    def image_quality(self) -> GPTImageQuality | None:
        quality = self.quality.lower()
        if quality in ['high', 'hd']:
            return GPTImageQuality.HIGH
        elif quality in ['medium', 'md', 'standart', 'standard']:
            return GPTImageQuality.MEDIUM
        elif quality in ['low']:
            return GPTImageQuality.LOW
        return None

    def __str__(self):
        return f"{self.name} | {self.size} | {self.quality}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'width', 'height', 'quality', 'provider'],
                name='unique_name_width_height_quality_img_draw'
            )
        ]

        verbose_name = "Модель генерации изображений"
        verbose_name_plural = "Модели генерации изображений"


class ImageEditModel(GPTImageModel):
    image_cost = models.DecimalField(
        "Стоимость редактирования одного изображения",
        max_digits=8,
        decimal_places=4
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'width', 'height', 'provider'],
                                    name='unique_name_width_height_image_edit')
        ]

        verbose_name = "Модель редактирования изображений"
        verbose_name_plural = "Модели редактирования изображений"


class VoiceRecognitionModel(GPTModel):
    voice_recognition_1_min_cost = models.DecimalField(
        "Стоимость за 1 минуту распознования голоса",
        max_digits=8,
        decimal_places=4,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'provider'], name='unique_name_voice_recognition_model')
        ]

        verbose_name = "Модель распознования голоса"
        verbose_name_plural = "Модели распознования голоса"


class ProfileGPTSettings(TimeStampModelMixin):
    provider = models.ForeignKey(Provider, models.CASCADE, verbose_name="Провайдер")

    profile = models.ForeignKey(
        Profile,
        models.CASCADE,
        verbose_name="Профиль",
        related_name="gpt_settings"
    )
    key = models.CharField(
        "Ключ провайдера",
        max_length=1024,
        blank=True
    )
    completions_model = models.ForeignKey(
        CompletionsModel,
        models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Модель обработки текста",

    )
    vision_model = models.ForeignKey(
        VisionModel,
        models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Модель обработки изображений",
    )
    image_draw_model = models.ForeignKey(
        ImageDrawModel,
        models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Модель рисования изображений",
    )
    image_edit_model = models.ForeignKey(
        ImageEditModel,
        models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Модель редактирования изображений",
    )
    voice_recognition_model = models.ForeignKey(
        VoiceRecognitionModel,
        models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Модель распознования голоса",
    )

    def get_key(self) -> str:
        if not self.key:
            return self.key
        return Fernet.decrypt(self.key)

    def set_key(self, key: str) -> None:
        if key == "":
            self.key = ""
        else:
            self.key = Fernet.encrypt(key)

    def __str__(self):
        return str(self.profile)

    class Meta:
        unique_together = ('profile', 'provider')

        verbose_name = "Настройка профиля GPT"
        verbose_name_plural = "Настройки профиля GPT"
