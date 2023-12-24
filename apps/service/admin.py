from django.contrib import admin

from apps.service.models import Service, Meme, Notify, City, Donations, TimeZone, Subscribe, WakeOnLanUserData, \
    Horoscope, Words, Tag, VideoCache, Promocode


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'value', 'update_datetime')


@admin.action(description="Проставить тип: видео")
def set_type_video(modeladmin, request, queryset):
    queryset.update(type="video")


@admin.action(description="Проставить тип: ссылка")
def set_type_link(modeladmin, request, queryset):
    queryset.update(type="link")


@admin.register(Meme)
class MemeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'preview_image', 'preview_link', 'author', 'approved', 'type', 'uses', 'inline_uses', 'link',
        'tg_file_id'
    )
    search_fields = ('name', 'link')
    list_filter = (('author', admin.RelatedOnlyFieldListFilter), 'type', 'approved',)
    actions = [set_type_video, set_type_link]


@admin.register(Notify)
class NotifyAdmin(admin.ModelAdmin):
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


@admin.register(Donations)
class DonationsAdmin(admin.ModelAdmin):
    list_display = ('username', 'amount', 'currency', 'message', 'date')


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('author', 'chat', 'channel_title', 'playlist_title', 'service', 'save_to_plex')
    list_filter = (
        ('author', admin.RelatedOnlyFieldListFilter), ('chat', admin.RelatedOnlyFieldListFilter), 'save_to_plex')
    search_fields = ('channel_title', 'playlist_title', 'last_video_id', 'last_videos_id')


@admin.register(VideoCache)
class VideoCacheAdmin(admin.ModelAdmin):
    list_display = ('filename',)


@admin.register(WakeOnLanUserData)
class WakeOnLanUserDataAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'ip', 'port', 'mac',)
    list_filter = (('author', admin.RelatedOnlyFieldListFilter),)


@admin.register(Horoscope)
class HoroscopeAdmin(admin.ModelAdmin):
    list_display = ('pk',)
    filter_horizontal = ('memes',)


@admin.register(Words)
class WordsAdmin(admin.ModelAdmin):
    list_display = ('id', 'm1', 'f1', 'n1', 'mm', 'fm', 'type')
    list_filter = ('type',)
    search_fields = ['id', 'm1', 'f1', 'n1', 'mm', 'fm', 'type']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_filter = (('chat', admin.RelatedOnlyFieldListFilter), ('users', admin.RelatedOnlyFieldListFilter))


@admin.register(Promocode)
class Promocode(admin.ModelAdmin):
    list_display = ('name', 'code', 'author', 'expiration', 'description', "is_personal")
    list_filter = ('name', 'author', "is_personal")
    search_fields = ('name', 'code', 'description')
