from django.contrib import admin
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils.html import format_html

from apps.bot.models import Profile, Chat, Bot, User, ChatSettings, UserSettings
from apps.service.mixins import TimeStampAdminMixin


class NoSpecificGroupFilter(admin.SimpleListFilter):
    title = 'Нет группы'
    parameter_name = 'no_specific_group'

    def lookups(self, request, model_admin):
        groups = Group.objects.all()
        return [(group.id, group.name) for group in groups]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.exclude(groups__id=self.value())
        return queryset


@admin.register(Profile)
class ProfileAdmin(TimeStampAdminMixin):
    list_display = ('name', 'surname', 'nickname_real', 'gender', 'birthday', 'city')
    fieldsets = (
        (
            'Profile Info',
            {
                'fields': ('name', 'surname', 'nickname_real', 'gender', 'birthday', 'city', 'avatar')
            }
        ),
        (
            'Other',
            {
                'fields': ('groups', 'settings')
            }
        ),
        (
            'API',
            {
                'fields': ('api_token',)
            }
        ),
        (
            'Chats',
            {
                'fields': ('get_chats', 'chats')
            }
        ),

    )

    list_filter = (
        'gender',
        ('city', admin.RelatedOnlyFieldListFilter),
        ('groups', admin.RelatedOnlyFieldListFilter),
        NoSpecificGroupFilter,
        'chats__name'
    )
    search_fields = ['name', 'surname', 'nickname_real', 'user__user_id']

    ordering = ["name", "surname"]

    readonly_fields = ['get_chats']

    @admin.display(description='Чаты 2')
    def get_chats(self, obj):
        chats = obj.chats.all()
        links = [
            format_html(
                '<a href="{url}">{name}</a>',
                url=reverse('admin:bot_chat_change', args=[profile.id]),
                name=str(profile)
            )
            for profile in chats
        ]
        return format_html("<br>".join(links))


@admin.register(User)
class UserAdmin(TimeStampAdminMixin):
    search_fields = ('profile__name', 'profile__surname', 'profile__nickname_real', 'nickname', 'user_id')
    list_display = ('show_user_id', 'show_url', 'platform', 'profile', 'nickname')
    list_filter = ('platform',)

    ordering = ["profile"]


@admin.register(Chat)
class ChatAdmin(TimeStampAdminMixin):
    search_fields = ('name', 'chat_id')
    list_display = ('id', 'name', 'platform', 'is_banned', 'kicked')
    list_filter = ('platform', 'kicked')

    ordering = ["name"]

    readonly_fields = ['get_users']

    @admin.display(description='Пользователи')
    def get_users(self, obj):
        profiles = obj.users.all()
        links = [
            format_html(
                '<a href="{url}">{name}</a>',
                url=reverse('admin:bot_profile_change', args=[profile.id]),
                name=str(profile)
            )
            for profile in profiles
        ]
        return format_html("<br>".join(links))


@admin.register(Bot)
class BotAdmin(TimeStampAdminMixin):
    list_display = ('name', 'platform',)
    list_filter = ('platform',)
    ordering = ["id"]


@admin.register(UserSettings)
class UserSettingsAdmin(TimeStampAdminMixin):
    pass


@admin.register(ChatSettings)
class ChatSettingsAdmin(TimeStampAdminMixin):
    pass
