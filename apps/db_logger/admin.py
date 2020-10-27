from __future__ import unicode_literals

import logging

from django.contrib import admin
from django.db import models
from django.forms import Textarea
from django.utils.html import format_html

from apps.db_logger.actions import set_debug, set_info, set_warning, set_error
from apps.db_logger.config import DJANGO_DB_LOGGER_ADMIN_LIST_PER_PAGE
from apps.db_logger.models import MovementLog, Logger


@admin.register(Logger)
class LoggerAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 15, 'cols': 150})},
    }

    list_display = ('create_datetime', 'logger_name', 'colored_level', 'sender', 'chat', 'user_msg', 'exception')
    list_filter = ('level',
                   ('sender', admin.RelatedOnlyFieldListFilter),
                   ('chat', admin.RelatedOnlyFieldListFilter),
                   'logger_name',)
    list_per_page = DJANGO_DB_LOGGER_ADMIN_LIST_PER_PAGE
    actions = [set_debug, set_info, set_warning, set_error]

    @staticmethod
    def colored_level(instance):
        if instance.level in [logging.NOTSET, logging.INFO, logging.DEBUG]:
            color = 'green'
        elif instance.level in [logging.WARNING]:
            color = 'orange'
        else:
            color = 'red'
        log_level = dict(instance.LOG_LEVELS)[instance.level]
        return format_html('<span style="color: {color};">{level}</span>', color=color, level=log_level)

    colored_level.short_description = 'Уровень'

    @staticmethod
    def traceback(instance):
        return format_html('<pre><code>{content}</code></pre>', content=instance.trace if instance.trace else '')



@admin.register(MovementLog)
class MovementLogAdmin(admin.ModelAdmin):
    readonly_fields = ('date',)
    list_display = ('date', 'imei', 'author', 'event', 'msg', 'success')
    list_filter = (('author', admin.RelatedOnlyFieldListFilter),)
