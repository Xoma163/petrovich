from django.contrib import admin

from apps.gpt.models import Preprompt, Usage, GPTSettings
from apps.service.mixins import TimeStampAdminMixin


# Register your models here.

@admin.register(Preprompt)
class GPTPrepromptAdmin(TimeStampAdminMixin):
    list_display = ('author', 'chat', 'provider', 'text')
    list_filter = (
        ('author', admin.RelatedOnlyFieldListFilter),
        ('chat', admin.RelatedOnlyFieldListFilter),
        'provider'
    )


@admin.register(Usage)
class GPTUsageAdmin(TimeStampAdminMixin):
    list_display = ('author', 'cost', 'provider')
    list_filter = (
        ('author', admin.RelatedOnlyFieldListFilter),
        'provider'
    )


@admin.register(GPTSettings)
class GPTSettingsAdmin(TimeStampAdminMixin):
    list_display = ('profile', 'chat_gpt_model', 'claude_model', 'grok_model')
