from django.contrib import admin

from apps.commands.gpt.actions import copy_completions_to_vision
from apps.commands.gpt.models import (
    Preprompt,
    Usage,
    ProfileGPTSettings,
    Provider,
    CompletionsModel,
    VisionModel,
    ImageDrawModel,
    ImageEditModel,
    VoiceRecognitionModel, GPTPreset
)
from apps.service.mixins import TimeStampAdminMixin, TopFieldsMixin


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )
    ordering = (
        'name',
    )


@admin.register(Preprompt)
class PrepromptAdmin(TimeStampAdminMixin):
    list_display = (
        'author',
        'provider',
        'chat',
        'text'
    )
    search_fields = (
        'author__name',
        'author__surname',
        'author__nickname_real'
    )
    list_filter = (
        'provider',
        ('author', admin.RelatedOnlyFieldListFilter),
        ('chat', admin.RelatedOnlyFieldListFilter),
    )
    list_select_related = (
        'author',
        'chat',
        'provider'
    )
    ordering = (
        'author',
        'chat',
    )


@admin.register(Usage)
class UsageAdmin(TimeStampAdminMixin):
    list_display = (
        'author',
        'provider',
        'model_name',
        'cost'
    )
    search_fields = (
        'author__name',
        'author__surname',
        'author__nickname_real'
    )
    list_filter = (
        'provider',
        ('author', admin.RelatedOnlyFieldListFilter),
    )
    list_select_related = (
        'provider',
        'author',
    )

    ordering = (
        '-created_at',
    )


@admin.register(CompletionsModel)
class CompletionModelAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "provider",
        "verbose_name",
        "is_default",
        "input_1m_token_cost",
        "input_cached_1m_token_cost",
        "output_1m_token_cost",
        "web_search_1k_token_cost"
    )
    list_editable = (
        "verbose_name",
        "input_1m_token_cost",
        "input_cached_1m_token_cost",
        "output_1m_token_cost",
        "web_search_1k_token_cost"
    )
    list_filter = (
        "provider",
        "is_default",
    )
    list_select_related = (
        "provider",
    )
    ordering = (
        'name',
    )

    actions = [copy_completions_to_vision]


@admin.register(VisionModel)
class VisionModelAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "provider",
        "verbose_name",
        "is_default",
        "input_1m_token_cost",
        "input_cached_1m_token_cost",
        "output_1m_token_cost",
        "web_search_1k_token_cost"
    )
    list_editable = (
        "verbose_name",
        "input_1m_token_cost",
        "input_cached_1m_token_cost",
        "output_1m_token_cost",
        "web_search_1k_token_cost"
    )
    list_filter = (
        "provider",
        "is_default",
    )
    list_select_related = (
        "provider",
    )
    ordering = (
        'name',
    )


@admin.register(ImageDrawModel)
class ImageDrawModelAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "provider",
        "verbose_name",
        "is_default",
        "image_cost",
        "width",
        "height",
        "quality"
    )
    list_filter = (
        "provider",
        "is_default",
    )
    list_select_related = (
        "provider",
    )
    ordering = (
        'name',
    )


@admin.register(ImageEditModel)
class ImageEditModelAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "provider",
        "verbose_name",
        "is_default",
        "image_cost",
        "width",
        "height"
    )
    list_filter = (
        "provider",
        "is_default",
    )
    list_select_related = (
        "provider",
    )
    ordering = (
        'name',
    )


@admin.register(VoiceRecognitionModel)
class VoiceRecognitionModelAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "provider",
        "verbose_name",
        "is_default",
        "voice_recognition_1_min_cost"
    )
    list_filter = (
        "provider",
        "is_default",
    )
    list_select_related = (
        "provider",
    )
    ordering = (
        'name',
    )


@admin.register(ProfileGPTSettings)
class ProfileGPTSettingsAdmin(TimeStampAdminMixin, TopFieldsMixin):
    TOP_ORDER_FIELDS = ["provider", "profile"]
    list_display = (
        'profile',
        'has_key',
        "provider",
        "completions_model",
        "vision_model",
        "image_draw_model",
        "image_edit_model",
        "voice_recognition_model"
    )
    search_fields = (
        'profile__name',
        'profile__surname',
        'profile__nickname_real'
    )
    list_filter = (
        "provider",
        ('profile', admin.RelatedOnlyFieldListFilter),
    )
    list_select_related = (
        "profile",
        "provider",
        "completions_model",
        "vision_model",
        "image_draw_model",
        "image_edit_model",
        "voice_recognition_model",
    )
    ordering = (
        'profile',
    )

    @admin.display(boolean=True, description='Есть ключ')
    def has_key(self, obj: ProfileGPTSettings) -> bool:
        return bool(obj.key)


@admin.register(GPTPreset)
class GPTPresetAdmin(TimeStampAdminMixin, TopFieldsMixin):
    TOP_ORDER_FIELDS = ["provider", "profile", "name", "description"]
    list_display = (
        "profile",
        "name",
        "description",
        "provider",
    )
    search_fields = (
        'profile__name',
        'profile__surname',
        'profile__nickname_real'
    )
    list_filter = (
        "provider",
        ('profile', admin.RelatedOnlyFieldListFilter),
    )
    list_select_related = (
        "profile",
        "provider",
        "completions_model",
        "vision_model",
        "image_draw_model",
        "image_edit_model",
        "voice_recognition_model",
    )
    ordering = (
        'profile',
    )
