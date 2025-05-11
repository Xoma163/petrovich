from django.contrib import admin

from apps.gpt.models import Preprompt, Usage, ProfileGPTSettings, Provider, CompletionsModel, VisionModel, \
    ImageDrawModel, ImageEditModel, VoiceRecognitionModel
from apps.service.mixins import TimeStampAdminMixin


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ('name',)


@admin.register(Preprompt)
class PrepromptAdmin(TimeStampAdminMixin):
    list_display = ('author', 'provider', 'chat', 'text')
    list_filter = (
        ('author', admin.RelatedOnlyFieldListFilter),
        ('chat', admin.RelatedOnlyFieldListFilter),
        'provider'
    )
    ordering = ('author', 'chat',)
    search_fields = ('author__name', 'author__surname', 'author__nickname_real')


@admin.register(Usage)
class UsageAdmin(TimeStampAdminMixin):
    list_display = ('author', 'provider', 'model_name', 'cost')
    list_filter = (
        'provider',
        ('author', admin.RelatedOnlyFieldListFilter),
    )
    ordering = ('-created_at',)
    search_fields = ('author__name', 'author__surname', 'author__nickname_real')


@admin.register(CompletionsModel)
class CompletionModelAdmin(admin.ModelAdmin):
    list_display = ("name", "provider", "verbose_name", "is_default")
    list_filter = ("is_default", "provider")
    ordering = ('name',)


@admin.register(VisionModel)
class VisionModelAdmin(admin.ModelAdmin):
    list_display = (
        "name", "provider", "verbose_name", "is_default", "prompt_1m_token_cost", "completion_1m_token_cost")
    list_filter = ("is_default", "provider")
    ordering = ('name',)


@admin.register(ImageDrawModel)
class ImageDrawModelAdmin(admin.ModelAdmin):
    list_display = ("name", "provider", "verbose_name", "is_default", "image_cost", "width", "height", "quality")
    list_filter = ("is_default", "provider")
    ordering = ('name',)


@admin.register(ImageEditModel)
class ImageEditModelAdmin(admin.ModelAdmin):
    list_display = ("name", "provider", "verbose_name", "is_default", "image_cost", "width", "height")
    list_filter = ("is_default", "provider")
    ordering = ('name',)


@admin.register(VoiceRecognitionModel)
class VoiceRecognitionModelAdmin(admin.ModelAdmin):
    list_display = ("name", "provider", "verbose_name", "is_default", "voice_recognition_1_min_cost")
    list_filter = ("is_default", "provider")
    ordering = ('name',)


class ProfileGPTSettingsInline(admin.StackedInline):
    model = ProfileGPTSettings
    can_delete = False
    extra = 0


@admin.register(ProfileGPTSettings)
class ProfileGPTSettingsAdmin(TimeStampAdminMixin):
    list_display = (
        'profile', 'has_key', "provider", "completions_model", "vision_model", "image_draw_model", "image_edit_model",
        "voice_recognition_model")
    list_filter = ("provider",)
    ordering = ('profile',)
    search_fields = ('profile__name', 'profile__surname', 'profile__nickname_real')

    @admin.display(boolean=True, description='Есть ключ')
    def has_key(self, obj: ProfileGPTSettings) -> bool:
        return bool(obj.key)
