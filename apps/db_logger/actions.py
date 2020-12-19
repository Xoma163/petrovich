import logging


def set_debug(model_admin, request, queryset):
    for entity in queryset:
        entity.level = logging.DEBUG
        entity.save()


set_debug.short_description = "Установить DEBUG"


def set_info(model_admin, request, queryset):
    for entity in queryset:
        entity.level = logging.INFO
        entity.save()


set_info.short_description = "Установить INFO"


def set_warning(model_admin, request, queryset):
    for entity in queryset:
        entity.level = logging.WARNING
        entity.save()


set_warning.short_description = "Установить WARNING"


def set_error(model_admin, request, queryset):
    for entity in queryset:
        entity.level = logging.ERROR
        entity.save()


set_error.short_description = "Установить ERROR"
