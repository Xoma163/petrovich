from django.contrib import admin

from apps.bot.models import Profile, Chat, Bot, User


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'surname', 'nickname_real', 'gender', 'birthday', 'city')
    fieldsets = (
        ('Информация о пользователе', {
            'fields': (
                'name', 'surname', 'nickname_real', 'gender', 'birthday', 'city', 'avatar'),
        }),
        ('Прочее', {
            'fields': ('groups', 'chats'),
        }),

    )

    list_filter = (
        'gender',
        ('city', admin.RelatedOnlyFieldListFilter),
        ('groups', admin.RelatedOnlyFieldListFilter),
        'chats__name',)
    search_fields = ['name', 'surname', 'nickname_real']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('show_user_id', 'show_url', 'platform', 'profile', 'nickname')


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'admin', 'need_reaction', 'platform', 'is_banned')
    list_filter = ('platform',)


@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'platform',)
    list_filter = ('platform',)
