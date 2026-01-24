from django.contrib import admin

from apps.commands.games.models import (
    PetrovichUser,
    PetrovichGame,
    Wordle
)
from apps.service.mixins import TimeStampAdminMixin


@admin.register(PetrovichUser)
class PetrovichUserAdmin(TimeStampAdminMixin):
    list_display = (
        'profile',
        'chat',
        'wins',
        'active',
    )
    search_fields = (
        'profile__name',
        'profile__surname',
        'profile__nickname_real'
    )
    list_filter = (
        ('profile', admin.RelatedOnlyFieldListFilter),
        ('chat', admin.RelatedOnlyFieldListFilter),
    )
    list_select_related = (
        'profile',
        'chat'
    )
    ordering = (
        "profile",
    )


@admin.register(PetrovichGame)
class PetrovichGameAdmin(TimeStampAdminMixin):
    list_display = (
        'profile',
        'chat',
    )
    search_fields = (
        'profile__name',
        'profile__surname',
        'profile__nickname_real'
    )
    list_filter = (
        ('profile', admin.RelatedOnlyFieldListFilter),
        ('chat', admin.RelatedOnlyFieldListFilter),
    )
    list_select_related = (
        'profile',
        'chat'
    )
    ordering = (
        '-created_at',
    )


@admin.register(Wordle)
class WordleAdmin(TimeStampAdminMixin):
    list_display = (
        'profile',
        'chat',
        'word',
        'steps',
        'hypotheses'
    )
    list_select_related = (
        'profile',
        'chat'
    )
    ordering = (
        "chat",
    )
