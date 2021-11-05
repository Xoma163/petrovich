from django.contrib import admin

from apps.games.models import Rate, Gamer, PetrovichUser, PetrovichGames, RouletteRate, BullsAndCowsSession


@admin.register(Gamer)
class GamerAdmin(admin.ModelAdmin):
    search_fields = ('profile',)
    list_display = ('profile', 'points', 'roulette_points')
    list_editable = ('points', 'roulette_points')
    list_filter = ('profile__platform',)


@admin.register(Rate)
class RateAdmin(admin.ModelAdmin):
    list_display = ('gamer', 'chat', 'rate')
    ordering = ('-chat',)


@admin.register(PetrovichUser)
class PetrovichUserAdmin(admin.ModelAdmin):
    list_display = ('profile', 'chat', 'wins', 'active',)
    list_filter = (('profile', admin.RelatedOnlyFieldListFilter), ('chat', admin.RelatedOnlyFieldListFilter),)


@admin.register(PetrovichGames)
class PetrovichGamesAdmin(admin.ModelAdmin):
    list_display = ('profile', 'date', 'chat',)
    list_filter = (('profile', admin.RelatedOnlyFieldListFilter), ('chat', admin.RelatedOnlyFieldListFilter),)


@admin.register(RouletteRate)
class RouletteRateAdmin(admin.ModelAdmin):
    list_display = ('gamer', 'chat', 'rate_on', 'rate',)


@admin.register(BullsAndCowsSession)
class BullsAndCowsSessionAdmin(admin.ModelAdmin):
    list_display = ('author', 'chat', 'number', 'steps',)
