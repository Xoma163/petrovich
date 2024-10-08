from django.contrib import admin

from apps.service.mixins import TimeStampAdminMixin
from apps.service.models import Service, Meme, Notify, City, Donation, TimeZone, Subscribe, Tag, VideoCache, \
    GPTPrePrompt, GPTUsage


@admin.register(Service)
class ServiceAdmin(TimeStampAdminMixin):
    list_display = ('name', 'value', 'update_datetime')


@admin.register(Meme)
class MemeAdmin(TimeStampAdminMixin):
    list_display = (
        'id', 'name', 'preview_image', 'preview_link', 'author', 'approved', 'type', 'uses', 'inline_uses', 'link',
        'tg_file_id', "for_trusted"
    )
    search_fields = ('name', 'link')
    list_filter = (('author', admin.RelatedOnlyFieldListFilter), 'type', 'approved', 'for_trusted')
    ordering = ["name"]

@admin.register(Notify)
class NotifyAdmin(TimeStampAdminMixin):
    list_display = ('id', 'date', 'crontab', 'text', 'user', 'chat')
    search_fields = ['date', 'crontab', 'text']
    list_filter = (('user', admin.RelatedOnlyFieldListFilter), ('chat', admin.RelatedOnlyFieldListFilter),)
    ordering = ["user"]


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'synonyms', 'timezone', 'lat', 'lon')
    ordering = ["name"]


@admin.register(TimeZone)
class TimeZoneAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name',)
    ordering = ["name"]


@admin.register(Donation)
class DonationAdmin(TimeStampAdminMixin):
    list_display = ('username', 'amount', 'currency', 'message', 'date')
    ordering = ['-date']


@admin.register(Subscribe)
class SubscribeAdmin(TimeStampAdminMixin):
    list_display = (
        'author',
        'chat',
        'channel_title',
        'playlist_title',
        'service',
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
        'service'
    )
    search_fields = ('channel_title', 'playlist_title', 'last_videos_id')
    ordering = ['channel_title']


@admin.register(VideoCache)
class VideoCacheAdmin(TimeStampAdminMixin):
    list_display = ('filename',)
    ordering = ['filename']


@admin.register(Tag)
class TagAdmin(TimeStampAdminMixin):
    list_display = ('name', 'chat')
    list_filter = (('chat', admin.RelatedOnlyFieldListFilter), ('users', admin.RelatedOnlyFieldListFilter))
    ordering = ['name']


@admin.register(GPTPrePrompt)
class GPTPrepromptAdmin(TimeStampAdminMixin):
    list_display = ('author', 'chat', 'provider', 'text')
    list_filter = (
        ('author', admin.RelatedOnlyFieldListFilter),
        ('chat', admin.RelatedOnlyFieldListFilter),
        'provider'
    )


@admin.register(GPTUsage)
class GPTUsageAdmin(TimeStampAdminMixin):
    list_display = ('author', 'cost',)
    list_filter = (
        ('author', admin.RelatedOnlyFieldListFilter),
    )
