from django.contrib import admin

from apps.bot.models import Profile, Chat, Bot, User


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'surname', 'nickname_real', 'gender', 'birthday', 'city')
    fieldsets = (
        (
            'Информация о профиле',
            {
                'fields': ('name', 'surname', 'nickname_real', 'gender', 'birthday', 'city', 'avatar')
            }
        ),
        (
            'Прочее',
            {
                'fields': ('groups', 'chats')
            }
        ),
        (
            'Настройки',
            {
                'fields': ('celebrate_bday',)
            }
        ),
        (
            'API',
            {
                'fields': ('api_token',)
            }
        ),

    )

    list_filter = (
        'gender',
        ('city', admin.RelatedOnlyFieldListFilter),
        ('groups', admin.RelatedOnlyFieldListFilter),
        'chats__name',)
    search_fields = ['name', 'surname', 'nickname_real']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ('profile__name', 'profile__surname', 'profile__nickname_real', 'nickname', 'user_id')
    list_display = ('show_user_id', 'show_url', 'platform', 'profile', 'nickname')
    list_filter = ('platform',)


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('id', 'name', 'admin', 'platform', 'is_banned')
    list_filter = ('platform',)


@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'platform',)
    list_filter = ('platform',)
