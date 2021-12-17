from django.contrib import admin

from apps.service.models import Service, Counter, Meme, Notify, City, \
    Donations, TimeZone, YoutubeSubscribe, WakeOnLanUserData, Horoscope, QuoteBook, Words, TaxiInfo


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'value', 'update_datetime')


@admin.register(Counter)
class CounterAdmin(admin.ModelAdmin):
    list_display = ('name', 'count', 'chat')
    list_filter = (('chat', admin.RelatedOnlyFieldListFilter),)


@admin.register(Meme)
class MemeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'preview_image', 'preview_link', 'author', 'approved', 'type', 'uses')
    search_fields = ('name',)
    list_filter = (('author', admin.RelatedOnlyFieldListFilter), 'type', 'approved')


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


@admin.register(YoutubeSubscribe)
class YoutubeSubscribeAdmin(admin.ModelAdmin):
    list_display = ('author', 'chat', 'title', 'date',)
    list_filter = (('author', admin.RelatedOnlyFieldListFilter), ('chat', admin.RelatedOnlyFieldListFilter),)


@admin.register(WakeOnLanUserData)
class WakeOnLanUserDataAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'ip', 'port', 'mac',)
    list_filter = (('author', admin.RelatedOnlyFieldListFilter),)


@admin.register(Horoscope)
class HoroscopeAdmin(admin.ModelAdmin):
    list_display = ('pk',)
    filter_horizontal = ('memes',)


@admin.register(QuoteBook)
class QuoteBookAdmin(admin.ModelAdmin):
    list_display = ('chat', 'profile', 'date', 'text')
    list_filter = (('chat', admin.RelatedOnlyFieldListFilter), ('profile', admin.RelatedOnlyFieldListFilter),)


@admin.register(Words)
class WordsAdmin(admin.ModelAdmin):
    list_display = ('id', 'm1', 'f1', 'n1', 'mm', 'fm', 'type')
    list_filter = ('type',)
    search_fields = ['id', 'm1', 'f1', 'n1', 'mm', 'fm', 'type']


@admin.register(TaxiInfo)
class TaxiInfoAdmin(admin.ModelAdmin):
    pass
