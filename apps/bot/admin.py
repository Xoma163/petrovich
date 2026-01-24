from django.contrib import admin
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe

from apps.bot.filters import NoSpecificRoleFilter
from apps.bot.inlines import ProfileSettingsInline, UserInline, ChatSettingsInline
from apps.bot.models import Profile, Chat, Bot, User, ChatSettings, ProfileSettings
from apps.commands.gpt.inlines import ProfileGPTSettingsInline
from apps.shared.mixins import TimeStampAdminMixin


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
        ('roles', admin.RelatedOnlyFieldListFilter),
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
                'fields': ('roles',)
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
        links = []
        for chat in chats:
            url = reverse('admin:bot_chat_change', args=[chat.id])
            name = escape(str(chat))
            links.append(f'<a href="{url}">{name}</a>')
        return mark_safe("<br/>".join(links)) if links else "-"

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
        links = []
        for profile in profiles:
            url = reverse('admin:bot_profile_change', args=[profile.id])
            safe_url = escape(url)
            safe_name = escape(str(profile))
            links.append(f'<a href="{safe_url}">{safe_name}</a>')
        return mark_safe("<br/>".join(links)) if links else "-"

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
        'celebrate_bday',
        'show_birthday_year',
        'use_mention'
    )
    list_editable = (
        'need_reaction',
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
        'celebrate_bday',
        'recognize_voice',
    )
    list_editable = (
        'no_mention',
        'celebrate_bday',
        'recognize_voice',
    )
    list_select_related = (
        "chat",
    )
    ordering = (
        "chat",
    )
