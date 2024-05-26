from django.contrib import admin

from apps.games.models import Gamer, Rate, PetrovichUser, PetrovichGames, RouletteRate, BullsAndCowsSession, Wordle
from apps.service.mixins import TimeStampAdminMixin


@admin.register(Gamer)
class GamerAdmin(TimeStampAdminMixin):
    search_fields = ('profile__name', 'profile__surname', 'profile__nickname_real')
    list_display = ('profile', 'points', 'roulette_points')
    list_editable = ('points', 'roulette_points')


@admin.register(Rate)
class RateAdmin(TimeStampAdminMixin):
    list_display = ('gamer', 'chat', 'rate')
    ordering = ('-chat',)


@admin.register(PetrovichUser)
class PetrovichUserAdmin(TimeStampAdminMixin):
    search_fields = ('profile__name', 'profile__surname', 'profile__nickname_real')
    list_display = ('profile', 'chat', 'wins', 'active',)
    list_filter = (('profile', admin.RelatedOnlyFieldListFilter), ('chat', admin.RelatedOnlyFieldListFilter),)


@admin.register(PetrovichGames)
class PetrovichGamesAdmin(TimeStampAdminMixin):
    search_fields = ('profile__name', 'profile__surname', 'profile__nickname_real')
    list_display = ('profile', 'date', 'chat',)
    list_filter = (('profile', admin.RelatedOnlyFieldListFilter), ('chat', admin.RelatedOnlyFieldListFilter),)


@admin.register(RouletteRate)
class RouletteRateAdmin(TimeStampAdminMixin):
    list_display = ('gamer', 'chat', 'rate_on', 'rate',)


@admin.register(BullsAndCowsSession)
class BullsAndCowsSessionAdmin(TimeStampAdminMixin):
    search_fields = ('profile__name', 'profile__surname', 'profile__nickname_real')
    list_display = ('profile', 'chat', 'number', 'steps',)


@admin.register(Wordle)
class WordleAdmin(TimeStampAdminMixin):
    list_display = ('profile', 'chat', 'word', 'steps', 'hypotheses')
