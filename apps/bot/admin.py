from django.contrib import admin
from django.contrib.auth.models import Group

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
            'Информация о профиле',
            {
                'fields': ('name', 'surname', 'nickname_real', 'gender', 'birthday', 'city', 'avatar')
            }
        ),
        (
            'Прочее',
            {
                'fields': ('groups', 'chats', 'settings')
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
        NoSpecificGroupFilter,
        'chats__name'
    )
    search_fields = ['name', 'surname', 'nickname_real', 'user__user_id']

    ordering = ["name", "surname"]


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
