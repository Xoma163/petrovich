from django.contrib import admin

from apps.bot.models import Users, Chat, Bot


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

        ('Отправка уведомлений', {
            'fields': ('imei', 'send_notify_to'),
        }),
    )

    list_filter = ('platform',
                   'gender',
                   ('city', admin.RelatedOnlyFieldListFilter),
                   ('groups', admin.RelatedOnlyFieldListFilter),
                   'chats__name',)
    search_fields = ['name', 'surname', 'nickname', 'nickname_real', 'user_id']


admin.site.register(Users, UserAdmin)


class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'admin', 'need_reaction', 'platform',)
    list_filter = ('platform',)


admin.site.register(Chat, ChatAdmin)


class BotAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'platform',)
    list_filter = ('platform',)


admin.site.register(Bot, BotAdmin)
