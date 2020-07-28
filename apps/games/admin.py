from django.contrib import admin

from apps.games.models import Rate, Gamer, PetrovichUser, PetrovichGames, TicTacToeSession, CodenamesUser, \
    CodenamesSession, RouletteRate


@admin.register(Gamer)
class GamerAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'tic_tac_toe_points', 'codenames_points', 'roulette_points')


@admin.register(Rate)
class RateAdmin(admin.ModelAdmin):
    list_display = ('gamer', 'chat', 'rate')
    ordering = ('-chat',)


@admin.register(PetrovichUser)
class PetrovichUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'chat', 'wins', 'active',)
    list_filter = (('user', admin.RelatedOnlyFieldListFilter), ('chat', admin.RelatedOnlyFieldListFilter),)


@admin.register(PetrovichGames)
class PetrovichGamesAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'chat',)
    list_filter = (('user', admin.RelatedOnlyFieldListFilter), ('chat', admin.RelatedOnlyFieldListFilter),)


@admin.register(TicTacToeSession)
class TicTacToeSessionAdmin(admin.ModelAdmin):
    list_display = ('user1', 'user2', 'board',)


@admin.register(CodenamesUser)
class CodenamesUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'chat', 'command', 'role', 'role_preference')
    list_filter = (('user', admin.RelatedOnlyFieldListFilter), ('chat', admin.RelatedOnlyFieldListFilter),)


@admin.register(CodenamesSession)
class CodenamesSessionAdmin(admin.ModelAdmin):
    list_display = ('chat', 'next_step', 'board')


@admin.register(RouletteRate)
class RouletteRateAdmin(admin.ModelAdmin):
    list_display = ('gamer', 'chat', 'rate_on', 'rate',)
