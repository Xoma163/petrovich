from django.contrib import admin
from django.db import models


class TimeStampModelMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлён")

    class Meta:
        abstract = True


class TimeStampAdminMixin(admin.ModelAdmin):
    EXTRA_FIELDS = ['created_at', 'updated_at']

    def __init__(self, model, admin_site):
        self.list_display = list(self.list_display) + self.EXTRA_FIELDS
        self.readonly_fields = list(self.readonly_fields) + self.EXTRA_FIELDS  # noqa
        self.list_filter = list(self.list_filter) + self.EXTRA_FIELDS  # noqa
        super().__init__(model, admin_site)


class TopFieldsMixin(admin.ModelAdmin):
    TOP_ORDER_FIELDS = []

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        for top_field in self.TOP_ORDER_FIELDS:
            fields.remove(top_field)
        return self.TOP_ORDER_FIELDS + fields
