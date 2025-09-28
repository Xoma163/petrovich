from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from apps.bot.filters import NoSpecificRoleFilter
from apps.bot.inlines import ProfileSettingsInline, UserInline, ChatSettingsInline
from apps.bot.models import Profile, Chat, Bot, User, ChatSettings, ProfileSettings
from apps.gpt.inlines import ProfileGPTSettingsInline
from apps.service.mixins import TimeStampAdminMixin


@admin.register(User)
class UserAdmin(TimeStampAdminMixin):
    list_display = (
        'show_user_id',
        'show_url',
        'platform',
        'profile',
        'nickname'
    )
    search_fields = (
        'profile__name',
        'profile__surname',
        'profile__nickname_real',
        'nickname',
        'user_id'
    )

    list_filter = (
        'platform',
    )
    list_select_related = (
        'profile',
    )
    ordering = (
        "profile",
    )


@admin.register(Profile)
class ProfileAdmin(TimeStampAdminMixin):
    list_display = (
        'name',
        'surname',
        'nickname_real',
        'gender',
        'birthday',
        'city',
        'get_chats_count'
    )
    search_fields = (
        'name',
        'surname',
        'nickname_real',
        'user__user_id',
        'user__nickname'
    )
    list_filter = (
        'gender',
        ('city', admin.RelatedOnlyFieldListFilter),
        ('groups', admin.RelatedOnlyFieldListFilter),
        NoSpecificRoleFilter,
        'chats__name'
    )
    list_select_related = (
        'city',
        'settings',
    )
    ordering = ("name", "surname")
    inlines = (
        ProfileSettingsInline,
        ProfileGPTSettingsInline,
        UserInline
    )
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
                'fields': ('groups',)
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
                'fields': ('get_chats_count', 'get_chats', 'chats')
            }
        ),
        (
            'Date',
            {
                'fields': ('created_at', 'updated_at')
            }
        ),
    )
    readonly_fields = ('get_chats', 'get_chats_count')

    @admin.display(description='Чаты')
    def get_chats(self, obj: Profile):
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

    @admin.display(description='Количество чатов')
    def get_chats_count(self, obj: Profile):
        return obj.chats.all().count()


@admin.register(Chat)
class ChatAdmin(TimeStampAdminMixin):
    list_display = (
        'id',
        'name',
        'platform',
        'is_banned',
        'kicked',
        'get_users_count'
    )
    search_fields = (
        'name',
        'chat_id'
    )
    list_filter = (
        'platform',
        'kicked'
    )
    list_select_related = (
        'settings',
    )
    ordering = (
        "name",
    )
    inlines = (ChatSettingsInline,)
    fieldsets = (
        (
            'Chat Info',
            {
                'fields': ('chat_id', 'name', 'platform', 'is_banned', 'kicked',)
            }
        ),
        (
            'Users',
            {
                'fields': ('get_users_count', 'get_users')
            }
        ),
        (
            'Date',
            {
                'fields': ('created_at', 'updated_at')
            }
        ),
    )
    readonly_fields = (
        'get_users_count',
        'get_users',
        'chat_id'
    )

    @admin.display(description='Пользователи')
    def get_users(self, obj: Chat):
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

    @admin.display(description='Количество пользователей')
    def get_users_count(self, obj: Chat):
        return obj.users.all().count()


@admin.register(Bot)
class BotAdmin(TimeStampAdminMixin):
    list_display = (
        'name',
        'platform',
    )
    list_filter = (
        'platform',
    )
    ordering = (
        "id",
    )


@admin.register(ProfileSettings)
class ProfileSettingsAdmin(TimeStampAdminMixin):
    list_display = (
        'profile',
        'need_reaction',
        'use_swear',
        'celebrate_bday',
        'show_birthday_year',
        'use_mention'
    )
    list_editable = (
        'need_reaction',
        'use_swear',
        'celebrate_bday',
        'show_birthday_year',
        'use_mention'
    )
    list_select_related = (
        'profile',
    )
    ordering = (
        "profile",
    )


@admin.register(ChatSettings)
class ChatSettingsAdmin(TimeStampAdminMixin):
    list_display = (
        'chat',
        'no_mention',
        'need_turett',
        'celebrate_bday',
        'recognize_voice',
        'time_conversion'
    )
    list_editable = (
        'no_mention',
        'need_turett',
        'celebrate_bday',
        'recognize_voice',
        'time_conversion'
    )
    list_select_related = (
        "chat",
    )
    ordering = (
        "chat",
    )
