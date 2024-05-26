from django.contrib import admin

from apps.games.models import Gamer, Rate, PetrovichUser, PetrovichGame, RouletteRate, BullsAndCowsSession, Wordle
from apps.service.mixins import TimeStampAdminMixin


@admin.register(Gamer)
class GamerAdmin(TimeStampAdminMixin):
    search_fields = ('profile__name', 'profile__surname', 'profile__nickname_real')
    list_display = ('profile', 'points', 'roulette_points')
    list_editable = ('points', 'roulette_points')

    ordering = ["profile"]


@admin.register(Rate)
class RateAdmin(TimeStampAdminMixin):
    list_display = ('gamer', 'chat', 'rate')
    ordering = ["chat", "created_at"]


@admin.register(PetrovichUser)
class PetrovichUserAdmin(TimeStampAdminMixin):
    search_fields = ('profile__name', 'profile__surname', 'profile__nickname_real')
    list_display = ('profile', 'chat', 'wins', 'active',)
    list_filter = (('profile', admin.RelatedOnlyFieldListFilter), ('chat', admin.RelatedOnlyFieldListFilter),)
    ordering = ["profile"]


@admin.register(PetrovichGame)
class PetrovichGameAdmin(TimeStampAdminMixin):
    search_fields = ('profile__name', 'profile__surname', 'profile__nickname_real')
    list_display = ('profile', 'chat',)
    list_filter = (('profile', admin.RelatedOnlyFieldListFilter), ('chat', admin.RelatedOnlyFieldListFilter),)
    ordering = ['-created_at']


@admin.register(RouletteRate)
class RouletteRateAdmin(TimeStampAdminMixin):
    list_display = ('gamer', 'chat', 'rate_on', 'rate',)


@admin.register(BullsAndCowsSession)
class BullsAndCowsSessionAdmin(TimeStampAdminMixin):
    search_fields = ('profile__name', 'profile__surname', 'profile__nickname_real')
    list_display = ('profile', 'chat', 'number', 'steps',)
    ordering = ["chat"]


@admin.register(Wordle)
class WordleAdmin(TimeStampAdminMixin):
    list_display = ('profile', 'chat', 'word', 'steps', 'hypotheses')
    ordering = ["chat"]
