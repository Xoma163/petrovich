from django.contrib import admin

from apps.games.models import Gamer, Rate, PetrovichUser, PetrovichGames, RouletteRate, BullsAndCowsSession, Wordle


@admin.register(Gamer)
class GamerAdmin(admin.ModelAdmin):
    search_fields = ('profile__name', 'profile__surname', 'profile__nickname_real')
    list_display = ('profile', 'points', 'roulette_points')
    list_editable = ('points', 'roulette_points')


@admin.register(Rate)
class RateAdmin(admin.ModelAdmin):
    list_display = ('gamer', 'chat', 'rate')
    ordering = ('-chat',)


@admin.register(PetrovichUser)
class PetrovichUserAdmin(admin.ModelAdmin):
    search_fields = ('profile__name', 'profile__surname', 'profile__nickname_real')
    list_display = ('profile', 'chat', 'wins', 'active',)
    list_filter = (('profile', admin.RelatedOnlyFieldListFilter), ('chat', admin.RelatedOnlyFieldListFilter),)


@admin.register(PetrovichGames)
class PetrovichGamesAdmin(admin.ModelAdmin):
    search_fields = ('profile__name', 'profile__surname', 'profile__nickname_real')
    list_display = ('profile', 'date', 'chat',)
    list_filter = (('profile', admin.RelatedOnlyFieldListFilter), ('chat', admin.RelatedOnlyFieldListFilter),)


@admin.register(RouletteRate)
class RouletteRateAdmin(admin.ModelAdmin):
    list_display = ('gamer', 'chat', 'rate_on', 'rate',)


@admin.register(BullsAndCowsSession)
class BullsAndCowsSessionAdmin(admin.ModelAdmin):
    search_fields = ('profile__name', 'profile__surname', 'profile__nickname_real')
    list_display = ('profile', 'chat', 'number', 'steps',)


@admin.register(Wordle)
class WordleAdmin(admin.ModelAdmin):
    list_display = ('profile', 'chat', 'word', 'steps', 'hypotheses')
