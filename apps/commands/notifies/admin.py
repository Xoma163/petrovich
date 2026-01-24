from django.contrib import admin

from apps.commands.notifies.models import Notify
from apps.shared.mixins import TimeStampAdminMixin


# Register your models here.
@admin.register(Notify)
class NotifyAdmin(TimeStampAdminMixin):
    list_display = (
        'id',
        'date',
        'crontab',
        'text',
        'user',
        'chat'
    )
    search_fields = (
        'date',
        'crontab',
        'text'
    )
    list_filter = (
        ('user', admin.RelatedOnlyFieldListFilter),
        ('chat', admin.RelatedOnlyFieldListFilter),
    )
    list_select_related = (
        'user',
        'chat'
    )
    ordering = (
        "user",
    )
