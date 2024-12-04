from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from apps.service.mixins import TimeStampAdminMixin
from apps.service.models import Service, Meme, Notify, City, Donation, TimeZone, Subscribe, Tag, VideoCache, \
    GPTPrePrompt, GPTUsage, SubscribeItem


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


class SubscribeInline(admin.TabularInline):
    model = Subscribe
    can_delete = False
    extra = 0


@admin.register(SubscribeItem)
class SubscribeItemAdmin(TimeStampAdminMixin):
    list_display = (
        'channel_title',
        'playlist_title',
        'service',
        'get_subscribes',
        'get_subscribes_count'
    )
    list_filter = (
        'service',
    )
    search_fields = ('channel_title', 'playlist_title', 'last_videos_id')
    ordering = ['channel_title']
    inlines = (SubscribeInline,)

    @admin.display(description='Подписки')
    def get_subscribes(self, obj: SubscribeItem):
        subscribes = obj.subscribes.all()
        links = [
            format_html(
                '<a href="{url}">{name}</a>',
                url=reverse('admin:service_subscribe_change', args=[subscribe.id]),
                name=str(subscribe)
            )
            for subscribe in subscribes
        ]
        return format_html("<br>".join(links))

    @admin.display(description='Количество подписок')
    def get_subscribes_count(self, obj: SubscribeItem):
        return obj.subscribes.all().count()

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
