from django.contrib import admin

from apps.gpt.models import Preprompt, Usage, ProfileGPTSettings, Provider, CompletionsModel, VisionModel, \
    ImageDrawModel, ImageEditModel, VoiceRecognitionModel
from apps.service.mixins import TimeStampAdminMixin


# ToDo: ещё 10 раз подумать над тем, какие поля я хочу видеть в админке и редактировать


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Preprompt)
class PrepromptAdmin(TimeStampAdminMixin):
    list_display = ('author', 'provider', 'chat', 'text')
    list_filter = (
        ('author', admin.RelatedOnlyFieldListFilter),
        ('chat', admin.RelatedOnlyFieldListFilter),
        'provider'
    )


@admin.register(Usage)
class UsageAdmin(TimeStampAdminMixin):
    list_display = ('author', 'provider', 'model_name', 'cost')
    list_filter = (
        'provider',
        ('author', admin.RelatedOnlyFieldListFilter),
    )


@admin.register(CompletionsModel)
class CompletionModelAdmin(admin.ModelAdmin):
    list_display = ("name", "provider", "verbose_name", "is_default")
    list_filter = ("is_default", "provider")


@admin.register(VisionModel)
class VisionModelAdmin(admin.ModelAdmin):
    list_display = (
        "name", "provider", "verbose_name", "is_default", "prompt_1m_token_cost", "completion_1m_token_cost")
    list_filter = ("is_default", "provider")


@admin.register(ImageDrawModel)
class ImageDrawModelAdmin(admin.ModelAdmin):
    list_display = ("name", "provider", "verbose_name", "is_default", "image_cost", "width", "height", "quality")
    list_filter = ("is_default", "provider")


@admin.register(ImageEditModel)
class ImageEditModelAdmin(admin.ModelAdmin):
    list_display = ("name", "provider", "verbose_name", "is_default", "image_cost", "width", "height")
    list_filter = ("is_default", "provider")


@admin.register(VoiceRecognitionModel)
class VoiceRecognitionModelAdmin(admin.ModelAdmin):
    list_display = ("name", "provider", "verbose_name", "is_default", "voice_recognition_1_min_cost")
    list_filter = ("is_default", "provider")


@admin.register(ProfileGPTSettings)
class ProfileGPTSettingsAdmin(TimeStampAdminMixin):
    list_display = (
        'profile', "provider", "completions_model", "vision_model", "image_draw_model", "image_edit_model",
        "voice_recognition_model")
    list_filter = ("provider",)
