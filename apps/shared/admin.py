from django.contrib import admin

from apps.shared.mixins import TimeStampAdminMixin
from apps.shared.models import Service, City, TimeZone


# Register your models here.

@admin.register(Service)
class ServiceAdmin(TimeStampAdminMixin):
    list_display = (
        'name',
        'value',
        'update_datetime'
    )


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'synonyms',
        'timezone',
        'lat',
        'lon'
    )
    search_fields = (
        'name',
    )
    ordering = (
        "name",
    )


@admin.register(TimeZone)
class TimeZoneAdmin(admin.ModelAdmin):
    list_display = (
        "name",
    )
    search_fields = (
        "name",
    )
    ordering = (
        "name",
    )
