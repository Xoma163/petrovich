from django.contrib import admin

from apps.service.mixins import TimeStampAdminMixin
from apps.service.models import Service, Meme, Notify, City, Donation, TimeZone, Subscribe, WakeOnLanUserData, \
    Words, Tag, VideoCache, Promocode, GPTPrePrompt, GPTUsage


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


@admin.register(Notify)
class NotifyAdmin(TimeStampAdminMixin):
    list_display = ('id', 'date', 'crontab', 'text', 'user', 'chat')
    search_fields = ['date', 'crontab', 'text']
    list_filter = (('user', admin.RelatedOnlyFieldListFilter), ('chat', admin.RelatedOnlyFieldListFilter),)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'synonyms', 'timezone', 'lat', 'lon')


@admin.register(TimeZone)
class TimeZoneAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name',)


@admin.register(Donation)
class DonationsAdmin(TimeStampAdminMixin):
    list_display = ('username', 'amount', 'currency', 'message', 'date')


@admin.register(Subscribe)
class SubscribeAdmin(TimeStampAdminMixin):
    list_display = ('author', 'chat', 'channel_title', 'playlist_title', 'service', 'save_to_plex')
    list_filter = (
        ('author', admin.RelatedOnlyFieldListFilter),
        ('chat', admin.RelatedOnlyFieldListFilter),
        'save_to_plex',
        'service')
    search_fields = ('channel_title', 'playlist_title', 'last_videos_id')


@admin.register(VideoCache)
class VideoCacheAdmin(TimeStampAdminMixin):
    list_display = ('filename',)


@admin.register(WakeOnLanUserData)
class WakeOnLanUserDataAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'ip', 'port', 'mac',)
    list_filter = (('author', admin.RelatedOnlyFieldListFilter),)


@admin.register(Words)
class WordsAdmin(admin.ModelAdmin):
    list_display = ('id', 'm1', 'f1', 'n1', 'mm', 'fm', 'type')
    list_filter = ('type',)
    search_fields = ['id', 'm1', 'f1', 'n1', 'mm', 'fm', 'type']


@admin.register(Tag)
class TagAdmin(TimeStampAdminMixin):
    list_display = ('name', 'chat')
    list_filter = (('chat', admin.RelatedOnlyFieldListFilter), ('users', admin.RelatedOnlyFieldListFilter))


@admin.register(Promocode)
class Promocode(TimeStampAdminMixin):
    list_display = ('name', 'code', 'author', 'expiration', 'description', "is_personal")
    list_filter = ('name', 'author', "is_personal")
    search_fields = ('name', 'code', 'description')


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
    list_display = ('created_at', 'author', 'cost',)
    list_filter = (
        ('author', admin.RelatedOnlyFieldListFilter),
    )
