from django.contrib import admin

from apps.commands.media_command.models import VideoCache
from apps.shared.mixins import TimeStampAdminMixin


@admin.register(VideoCache)
class VideoCacheAdmin(TimeStampAdminMixin):
    list_display = (
        'filename',
        'source_url',
    )
    ordering = (
        'filename',
    )
