from django.contrib import admin
from django.contrib.postgres import fields
from django_json_widget.widgets import JSONEditorWidget

from apps.service.models import Service, Counter, Cat, Meme, Notify, City, \
    Donations, TimeZone, YoutubeSubscribe, WakeOnLanUserData, Horoscope, QuoteBook, Words, TaxiInfo


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'value', 'update_datetime')


@admin.register(Counter)
class CounterAdmin(admin.ModelAdmin):
    list_display = ('name', 'count', 'chat')
    list_filter = (('chat', admin.RelatedOnlyFieldListFilter),)


@admin.register(Cat)
class CatAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'preview', 'author', 'to_send')
    list_filter = (('author', admin.RelatedOnlyFieldListFilter), 'to_send',)


@admin.register(Meme)
class MemeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'preview_image', 'preview_link', 'author', 'approved', 'type', 'uses')
    search_fields = ['name', 'link']
    list_filter = (('author', admin.RelatedOnlyFieldListFilter), 'type', 'approved')


@admin.register(Notify)
class NotifyAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'text', 'author', 'chat', 'repeat')
    search_fields = ['date', 'text', 'text_for_filter']
    list_filter = (('author', admin.RelatedOnlyFieldListFilter), ('chat', admin.RelatedOnlyFieldListFilter), 'repeat',)
    formfield_overrides = {
        fields.JSONField: {'widget': JSONEditorWidget},
    }


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'synonyms', 'timezone', 'lat', 'lon')


@admin.register(TimeZone)
class TimeZoneAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Donations)
class DonationsAdmin(admin.ModelAdmin):
    list_display = ('username', 'amount', 'currency', 'message', 'date')


@admin.register(YoutubeSubscribe)
class YoutubeSubscribeAdmin(admin.ModelAdmin):
    list_display = ('author', 'chat', 'title', 'date',)
    list_filter = (('author', admin.RelatedOnlyFieldListFilter), ('chat', admin.RelatedOnlyFieldListFilter),)


@admin.register(WakeOnLanUserData)
class WakeOnLanUserDataAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'ip', 'port', 'mac',)
    list_filter = (('user', admin.RelatedOnlyFieldListFilter),)


@admin.register(Horoscope)
class HoroscopeAdmin(admin.ModelAdmin):
    list_display = ('pk',)
    filter_horizontal = ('memes',)


@admin.register(QuoteBook)
class QuoteBookAdmin(admin.ModelAdmin):
    list_display = ('chat', 'user', 'date', 'text')
    list_filter = (('chat', admin.RelatedOnlyFieldListFilter), ('user', admin.RelatedOnlyFieldListFilter),)


@admin.register(Words)
class WordsAdmin(admin.ModelAdmin):
    list_display = ('id', 'm1', 'f1', 'n1', 'mm', 'fm', 'type')
    list_filter = ('type',)
    search_fields = ['id', 'm1', 'f1', 'n1', 'mm', 'fm', 'type']


class JsonAdmin(admin.ModelAdmin):
    formfield_overrides = {
        fields.JSONField: {'widget': JSONEditorWidget},
    }


@admin.register(TaxiInfo)
class TaxiInfoAdmin(JsonAdmin):
    pass
