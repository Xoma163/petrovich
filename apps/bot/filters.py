from django.contrib import admin
from django.contrib.auth.models import Group


class NoSpecificRoleFilter(admin.SimpleListFilter):
    title = 'Нет роли'
    parameter_name = 'no_specific_role'

    def lookups(self, request, model_admin):
        groups = Group.objects.all()
        return [(group.id, group.name) for group in groups]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.exclude(groups__id=self.value())
        return queryset
