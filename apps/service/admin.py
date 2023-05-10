from django.contrib import admin

from apps.service.models import *


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'value', 'update_datetime')


@admin.register(Meme)
class MemeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'preview_image', 'preview_link', 'author', 'approved', 'type', 'uses', 'link', 'tg_file_id')
    search_fields = ('name',)
    list_filter = (('author', admin.RelatedOnlyFieldListFilter), 'type', 'approved',)


@admin.register(Notify)
class NotifyAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'crontab', 'text', 'user', 'chat', 'repeat')
    search_fields = ['date', 'crontab', 'text', 'text_for_filter']
    list_filter = (('user', admin.RelatedOnlyFieldListFilter), ('chat', admin.RelatedOnlyFieldListFilter), 'repeat',)


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
    list_display = ('author', 'chat', 'title', 'service', 'date',)
    list_filter = (('author', admin.RelatedOnlyFieldListFilter), ('chat', admin.RelatedOnlyFieldListFilter),)


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


@admin.register(TaxiInfo)
class TaxiInfoAdmin(admin.ModelAdmin):
    pass


@admin.register(Tag)
class Tag(admin.ModelAdmin):
    list_filter = (('chat', admin.RelatedOnlyFieldListFilter), ('users', admin.RelatedOnlyFieldListFilter))
