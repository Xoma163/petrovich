from django.contrib import admin

from apps.service.inlines import SubscribeInline
from apps.service.mixins import TimeStampAdminMixin
from apps.service.models import (
    Service,
    Meme,
    Notify,
    City,
    Donation,
    TimeZone,
    Subscribe,
    Tag,
    VideoCache,
    SubscribeItem
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


@admin.register(Donation)
class DonationAdmin(TimeStampAdminMixin):
    list_display = (
        'username',
        'amount',
        'currency',
        'message',
        'date'
    )
    ordering = (
        '-date',
    )






@admin.register(SubscribeItem)
class SubscribeItemAdmin(TimeStampAdminMixin):
    list_display = (
        'channel_title',
        'playlist_title',
        'service',
        'get_subscribes_count',
        'save_to_disk_admin',
        'high_resolution_admin',
        'force_cache_admin',
    )
    list_filter = (
        'service',
        ('subscribes__chat', admin.RelatedOnlyFieldListFilter),
    )
    search_fields = (
        'channel_title',
        'playlist_title',
        'last_videos_id'
    )
    inlines = (
        SubscribeInline,
    )
    ordering = (
        'channel_title',
    )

    @admin.display(description='Количество подписок')
    def get_subscribes_count(self, obj: SubscribeItem) -> int:
        return obj.subscribes.all().count()

    @admin.display(description='Сохранять на диск', boolean=True)
    def save_to_disk_admin(self, obj: SubscribeItem) -> bool:
        return obj.save_to_disk

    @admin.display(description='Высокое разрешение', boolean=True)
    def high_resolution_admin(self, obj: SubscribeItem) -> bool:
        return obj.high_resolution

    @admin.display(description='Принудительно кэшировать', boolean=True)
    def force_cache_admin(self, obj: SubscribeItem) -> bool:
        return obj.force_cache


@admin.register(Subscribe)
class SubscribeAdmin(TimeStampAdminMixin):
    list_display = (
        'author',
        'chat',
        'subscribe_item',
        'save_to_disk',
        'high_resolution',
        'force_cache',
    )
    list_filter = (
        ('author', admin.RelatedOnlyFieldListFilter),
        ('chat', admin.RelatedOnlyFieldListFilter),
        'save_to_disk',
        'high_resolution',
        'force_cache',
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


@admin.register(Tag)
class TagAdmin(TimeStampAdminMixin):
    list_display = (
        'name',
        'chat'
    )
    list_filter = (
        ('chat', admin.RelatedOnlyFieldListFilter),
        ('users', admin.RelatedOnlyFieldListFilter)
    )
    list_select_related = (
        'chat',
    )
    ordering = (
        'name',
    )
