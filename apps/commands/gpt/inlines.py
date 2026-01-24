from django.contrib import admin

from apps.commands.gpt.models import ProfileGPTSettings


class ProfileGPTSettingsInline(admin.StackedInline):
    model = ProfileGPTSettings
    can_delete = False
    extra = 0
