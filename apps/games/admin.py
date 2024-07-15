from django.contrib import admin

from apps.games.models import PetrovichUser, PetrovichGame, Wordle
from apps.service.mixins import TimeStampAdminMixin


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


@admin.register(Wordle)
class WordleAdmin(TimeStampAdminMixin):
    list_display = ('profile', 'chat', 'word', 'steps', 'hypotheses')
    ordering = ["chat"]
