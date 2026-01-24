from django.contrib import admin

from apps.service.mixins import TimeStampAdminMixin
from apps.service.models import (
    Service,
    Meme,
    Notify,
    City,
    TimeZone,
    VideoCache,
)


@admin.register(Service)
class ServiceAdmin(TimeStampAdminMixin):
    list_display = (
        'name',
        'value',
        'update_datetime'
    )


@admin.register(Meme)
class MemeAdmin(TimeStampAdminMixin):
    list_display = (
        'id',
        'name',
        'author',
        'approved',
        'type',
        'uses',
        'inline_uses',
        'link',
        'has_tg_file_id',
        "for_trusted"
    )
    search_fields = (
        'name',
        'link'
    )
    list_filter = (
        ('author', admin.RelatedOnlyFieldListFilter),
        'type',
        'approved',
        'for_trusted',
        ('file', admin.EmptyFieldListFilter)
    )
    list_select_related = (
        'author',
    )
    ordering = (
        "name",
    )

    @admin.display(description="Есть tg_file_id", boolean=True)
    def has_tg_file_id(self, obj: Meme) -> bool:
        return bool(obj.tg_file_id)

    @admin.display(description="Есть файл", boolean=True)
    def has_file(self, obj: Meme) -> bool:
        return bool(obj.file)


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


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'synonyms',
        'timezone',
        'lat',
        'lon'
    )
    search_fields = (
        'name',
    )
    ordering = (
        "name",
    )


@admin.register(TimeZone)
class TimeZoneAdmin(admin.ModelAdmin):
    list_display = (
        "name",
    )
    search_fields = (
        "name",
    )
    ordering = (
        "name",
    )

@admin.register(VideoCache)
class VideoCacheAdmin(TimeStampAdminMixin):
    list_display = (
        'filename',
        'original_url',
    )
    ordering = (
        'filename',
    )
