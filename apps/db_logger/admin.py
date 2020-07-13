from __future__ import unicode_literals

import logging

from django.contrib import admin
from django.db import models
from django.forms import Textarea
from django.utils.html import format_html

from apps.db_logger.config import DJANGO_DB_LOGGER_ADMIN_LIST_PER_PAGE
from apps.db_logger.models import MovementLog, Logger


class LoggerAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 15, 'cols': 150})},
    }

    list_display = ('create_datetime_format', 'logger_name', 'colored_level', 'sender', 'chat', 'user_msg', 'exception')
    list_filter = ('level',
                   ('sender', admin.RelatedOnlyFieldListFilter),
                   ('chat', admin.RelatedOnlyFieldListFilter))
    list_per_page = DJANGO_DB_LOGGER_ADMIN_LIST_PER_PAGE

    def colored_level(self, instance):
        if instance.level in [logging.NOTSET, logging.INFO, logging.DEBUG]:
            color = 'green'
        elif instance.level in [logging.WARNING]:
            color = 'orange'
        else:
            color = 'red'
        log_level = dict(instance.LOG_LEVELS)[instance.level]
        return format_html('<span style="color: {color};">{level}</span>', color=color, level=log_level)

    colored_level.short_description = 'Уровень'

    def traceback(self, instance):
        return format_html('<pre><code>{content}</code></pre>', content=instance.trace if instance.trace else '')

    def create_datetime_format(self, instance):
        return instance.create_datetime.strftime('%d.%m.%Y %X')

    create_datetime_format.short_description = "Дата создания"


@admin.register(Logger)
class LoggerAdmin(LoggerAdmin):
    pass


@admin.register(MovementLog)
class LogAdmin(admin.ModelAdmin):
    readonly_fields = ('date',)
    list_display = ('date', 'imei', 'author', 'event', 'msg', 'success')
    list_filter = (('author', admin.RelatedOnlyFieldListFilter),)
