from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.bot.models import Profile, Chat
from apps.commands.gpt.enums import (
    GPTProviderEnum,
    GPTImageFormat,
    GPTImageQuality,
    GPTReasoningEffortLevel,
    GPTVerbosityLevel,
)
from apps.shared.mixins import TimeStampModelMixin
from apps.shared.utils.fernet import Fernet


class Provider(models.Model):
    name = models.CharField(
        "Провайдер",
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

    author = models.ForeignKey(Profile, models.CASCADE, verbose_name="Профиль автора", null=True, blank=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name="Чат", null=True, blank=True)
    text = models.TextField("Текст препромпта", blank=True)

    def __str__(self):
        return f"{self.author} | {self.chat} | {self.provider}"

    class Meta:
        verbose_name = "Препромпт"
        verbose_name_plural = "Препромпты"
        unique_together = ("author", "chat", "provider")


class Usage(TimeStampModelMixin):
    provider = models.ForeignKey(Provider, models.CASCADE, verbose_name="Провайдер")

    author = models.ForeignKey(Profile, models.CASCADE, verbose_name="Профиль автора", null=True, db_index=True)
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
    is_default = models.BooleanField(default=False, verbose_name="Модель по умолчанию")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Если модель сохраняется с полем is_default, значит сбрасываем всем остальным поле default
        if self.is_default:
            self.__class__.objects.filter(provider=self.provider, is_default=True).exclude(id=self.id).update(
                is_default=False
            )
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class GPTCompletionsVisionModel(GPTModel):
    input_1m_token_cost = models.DecimalField(
        "Стоимость за 1млн. входных токенов",
        max_digits=8,
        decimal_places=4,
    )
    input_cached_1m_token_cost = models.DecimalField(
        "Стоимость за 1млн. входных токенов (кэшированных)",
        max_digits=8,
        decimal_places=4,
    )
    output_1m_token_cost = models.DecimalField(
        "Стоимость за 1млн. выходных токенов",
        max_digits=8,
        decimal_places=4,
    )
    web_search_1k_token_cost = models.DecimalField(
        "Стоимость за 1тыс. поисковых токенов",
        max_digits=8,
        decimal_places=4,
    )

    class Meta:
        abstract = True


class CompletionsModel(GPTCompletionsVisionModel):
    is_enabled_for_oauth = models.BooleanField(default=False, verbose_name="Доступна через OpenAI OAuth")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["name", "provider"], name="unique_name_completion_model")]

        verbose_name = "Модель обработки текста"
        verbose_name_plural = "Модели обработки текста"


class VisionModel(GPTCompletionsVisionModel):
    class Meta:
        constraints = [models.UniqueConstraint(fields=["name", "provider"], name="unique_name_vision_model")]

        verbose_name = "Модель обработки изображений"
        verbose_name_plural = "Модели обработки изображений"


class GPTImageModel(GPTModel):
    width = models.PositiveSmallIntegerField("Ширина изображения")
    height = models.PositiveSmallIntegerField("Высота изображения")

    @property
    def size(self) -> str:
        return f"{self.width}x{self.height}"

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
    image_cost = models.DecimalField("Стоимость генерации одного изображения", max_digits=8, decimal_places=4)
    quality = models.CharField("Название качества модели в API", max_length=32)

    @property
    def image_quality(self) -> GPTImageQuality | None:
        quality = self.quality.lower()
        if quality in ["high", "hd"]:
            return GPTImageQuality.HIGH
        elif quality in ["medium", "md", "standart", "standard"]:
            return GPTImageQuality.MEDIUM
        elif quality in ["low"]:
            return GPTImageQuality.LOW
        return None

    def __str__(self):
        return f"{self.name} | {self.size} | {self.quality}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "width", "height", "quality", "provider"],
                name="unique_name_width_height_quality_img_draw",
            )
        ]

        verbose_name = "Модель генерации изображений"
        verbose_name_plural = "Модели генерации изображений"


class ImageEditModel(GPTImageModel):
    image_cost = models.DecimalField("Стоимость редактирования одного изображения", max_digits=8, decimal_places=4)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "width", "height", "provider"], name="unique_name_width_height_image_edit"
            )
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
        constraints = [models.UniqueConstraint(fields=["name", "provider"], name="unique_name_voice_recognition_model")]

        verbose_name = "Модель распознования голоса"
        verbose_name_plural = "Модели распознования голоса"


class ProfileGPTBaseSettings(TimeStampModelMixin):
    provider = models.ForeignKey(Provider, models.CASCADE, verbose_name="Провайдер")

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

    gpt_5_settings_reasoning_effort_level = models.CharField(
        "Уровень рассуждений моделей семейства gpt-5",
        null=True,
        blank=True,
        max_length=32,
        choices=[(effort_level.value, effort_level.name) for effort_level in GPTReasoningEffortLevel],  # noqa
    )
    gpt_5_settings_verbosity_level = models.CharField(
        "Уровень многословности моделей семейства gpt-5",
        null=True,
        blank=True,
        max_length=32,
        choices=[(verbosity_level.value, verbosity_level.name) for verbosity_level in GPTVerbosityLevel],  # noqa
    )
    gpt_5_settings_web_search = models.BooleanField("Поиск информации в интернете", null=True)
    use_debug = models.BooleanField("Дебаг режим", null=True)
    use_stream = models.BooleanField("Использовать режим потокового вывода", null=True)

    def clean(self):
        super().clean()
        models_to_check = {
            "completions_model": self.completions_model,
            "image_draw_model": self.image_draw_model,
            "image_edit_model": self.image_edit_model,
            "vision_model": self.vision_model,
            "voice_recognition_model": self.voice_recognition_model,
        }

        errors = {}
        error_template = "Провайдер модели ({provider_model}) не совпадает с провайдером настроек ({provider_self})."
        for model_name, model_instance in models_to_check.items():
            if model_instance and model_instance.provider != self.provider:
                errors[model_name] = error_template.format(
                    provider_model=model_instance.provider, provider_self=self.provider
                )
        if len(errors) > 0:
            raise ValidationError(errors)

    class Meta:
        abstract = True


class ProfileGPTSettings(ProfileGPTBaseSettings):
    class AuthType(models.TextChoices):
        API_KEY = "api_key", "API key"
        OAUTH_DEVICE = "oauth_device", "OpenAI OAuth (device)"

    key = models.CharField("Ключ провайдера", max_length=1024, blank=True)
    auth_type = models.CharField(
        "Тип авторизации",
        max_length=32,
        blank=True,
        choices=AuthType.choices,
        default="",
    )
    oauth_access_token = models.TextField("OAuth access token", blank=True)
    oauth_refresh_token = models.TextField("OAuth refresh token", blank=True)
    oauth_id_token = models.TextField("OAuth id token", blank=True)
    oauth_account_id = models.CharField("OAuth account id", max_length=255, blank=True)
    oauth_expires_at = models.DateTimeField("OAuth token expires at", null=True, blank=True)
    oauth_last_refresh_at = models.DateTimeField("OAuth last refresh at", null=True, blank=True)
    oauth_last_error = models.CharField("OAuth last error", max_length=1024, blank=True)

    profile = models.ForeignKey(Profile, models.CASCADE, verbose_name="Профиль", related_name="gpt_settings")

    def get_key(self) -> str:
        if not self.key:
            return self.key
        return Fernet.decrypt(self.key)

    def set_key(self, key: str) -> None:
        if key == "":
            self.key = ""
            if self.auth_type == self.AuthType.API_KEY:
                self.auth_type = self.AuthType.OAUTH_DEVICE if self.has_oauth_credentials() else ""
        else:
            self.key = Fernet.encrypt(key)
            self.auth_type = self.AuthType.API_KEY

    def has_key(self) -> bool:
        return bool(self.key)

    def get_oauth_access_token(self) -> str:
        if not self.oauth_access_token:
            return ""
        return Fernet.decrypt(self.oauth_access_token)

    def set_oauth_access_token(self, token: str) -> None:
        self.oauth_access_token = Fernet.encrypt(token) if token else ""

    def get_oauth_refresh_token(self) -> str:
        if not self.oauth_refresh_token:
            return ""
        return Fernet.decrypt(self.oauth_refresh_token)

    def set_oauth_refresh_token(self, token: str) -> None:
        self.oauth_refresh_token = Fernet.encrypt(token) if token else ""

    def get_oauth_id_token(self) -> str:
        if not self.oauth_id_token:
            return ""
        return Fernet.decrypt(self.oauth_id_token)

    def set_oauth_id_token(self, token: str) -> None:
        self.oauth_id_token = Fernet.encrypt(token) if token else ""

    def has_oauth_credentials(self) -> bool:
        return bool(self.oauth_access_token or self.oauth_refresh_token)

    def has_any_auth(self) -> bool:
        return self.has_key() or self.has_oauth_credentials()

    def get_active_auth_type(self) -> str | None:
        if self.auth_type == self.AuthType.OAUTH_DEVICE and self.has_oauth_credentials():
            return self.AuthType.OAUTH_DEVICE
        if self.auth_type == self.AuthType.API_KEY and self.has_key():
            return self.AuthType.API_KEY
        if self.has_key():
            return self.AuthType.API_KEY
        if self.has_oauth_credentials():
            return self.AuthType.OAUTH_DEVICE
        return None

    def set_oauth_tokens(
        self,
        access_token: str,
        refresh_token: str,
        id_token: str = "",
        account_id: str = "",
        expires_at=None,
        last_refresh_at=None,
    ) -> None:
        self.set_oauth_access_token(access_token)
        self.set_oauth_refresh_token(refresh_token)
        self.set_oauth_id_token(id_token)
        self.oauth_account_id = account_id or ""
        self.oauth_expires_at = expires_at
        self.oauth_last_refresh_at = last_refresh_at or timezone.now()
        self.oauth_last_error = ""
        self.auth_type = self.AuthType.OAUTH_DEVICE

    def clear_oauth_tokens(self) -> None:
        self.oauth_access_token = ""
        self.oauth_refresh_token = ""
        self.oauth_id_token = ""
        self.oauth_account_id = ""
        self.oauth_expires_at = None
        self.oauth_last_refresh_at = None
        self.oauth_last_error = ""
        if self.auth_type == self.AuthType.OAUTH_DEVICE:
            self.auth_type = self.AuthType.API_KEY if self.has_key() else ""

    def oauth_needs_refresh(self, safety_margin_seconds: int = 300) -> bool:
        if not self.has_oauth_credentials():
            return False
        if not self.oauth_expires_at:
            return True
        return self.oauth_expires_at <= timezone.now() + timedelta(seconds=safety_margin_seconds)

    def __str__(self):
        return str(self.profile)

    class Meta:
        unique_together = ("profile", "provider")

        verbose_name = "Настройка профиля GPT"
        verbose_name_plural = "Настройки профиля GPT"


class GPTPreset(ProfileGPTBaseSettings):
    name = models.CharField("Название", max_length=255)
    description = models.CharField("Описание", max_length=1023, blank=True, null=True)
    profile = models.ForeignKey(Profile, models.CASCADE, verbose_name="Профиль", related_name="gpt_presets")
    preprompt_text = models.TextField("Текст препромпта", blank=True, null=True)

    def __str__(self):
        return f"{self.profile} | {self.name}"

    class Meta:
        unique_together = ("profile", "provider", "name")

        verbose_name = "Пресет GPT"
        verbose_name_plural = "Пресеты GPT"
