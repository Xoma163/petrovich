from django.contrib import admin

from apps.bot.models import (
    User,
    ProfileSettings,
    ChatSettings
)


class UserInline(admin.StackedInline):
    model = User
    can_delete = False
    extra = 0


class ProfileSettingsInline(admin.StackedInline):
    model = ProfileSettings
    can_delete = False
    extra = 0


class ChatSettingsInline(admin.StackedInline):
    model = ChatSettings
    can_delete = False
    extra = 0
