from django.contrib import admin

from apps.service.models import Subscribe


class SubscribeInline(admin.TabularInline):
    model = Subscribe
    can_delete = False
    extra = 0
