from django.contrib import admin

from apps.bot.models import Profile, Chat, Bot, User, ChatSettings, UserSettings
from apps.service.mixins import TimeStampAdminMixin


@admin.register(Profile)
class ProfileAdmin(TimeStampAdminMixin):
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
                'fields': ('groups', 'chats', 'settings', 'gamer')
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
    search_fields = ['name', 'surname', 'nickname_real', 'user_id']


@admin.register(User)
class UserAdmin(TimeStampAdminMixin):
    search_fields = ('profile__name', 'profile__surname', 'profile__nickname_real', 'nickname', 'user_id')
    list_display = ('show_user_id', 'show_url', 'platform', 'profile', 'nickname')
    list_filter = ('platform',)


@admin.register(Chat)
class ChatAdmin(TimeStampAdminMixin):
    search_fields = ('name', 'chat_id')
    list_display = ('id', 'name', 'platform', 'is_banned', 'kicked')
    list_filter = ('platform', 'kicked')


@admin.register(Bot)
class BotAdmin(TimeStampAdminMixin):
    list_display = ('name', 'platform',)
    list_filter = ('platform',)


@admin.register(UserSettings)
class UserSettingsAdmin(TimeStampAdminMixin):
    pass


@admin.register(ChatSettings)
class ChatSettingsAdmin(TimeStampAdminMixin):
    pass
