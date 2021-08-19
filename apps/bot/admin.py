from django.contrib import admin

from apps.bot.models import Users, Chat, Bot


@admin.register(Users)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'show_user_id', 'show_url', 'name', 'surname', 'nickname', 'nickname_real', 'gender', 'birthday', 'city')
    list_display_links = ('show_user_id',)
    fieldsets = (
        ('Информация о пользователе', {
            'fields': (
                'user_id', 'name', 'surname', 'nickname', 'nickname_real', 'gender', 'birthday', 'city', 'avatar'),
        }),
        ('Прочее', {
            'fields': ('groups', 'chats', 'platform'),
        }),

    )

    list_filter = ('platform',
                   'gender',
                   ('city', admin.RelatedOnlyFieldListFilter),
                   ('groups', admin.RelatedOnlyFieldListFilter),
                   'chats__name',)
    search_fields = ['name', 'surname', 'nickname', 'nickname_real', 'user_id']


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'admin', 'need_reaction', 'platform', 'is_banned')
    list_filter = ('platform',)


@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'platform',)
    list_filter = ('platform',)
