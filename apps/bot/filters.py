from django.contrib import admin

from apps.bot.models import Role


class NoSpecificRoleFilter(admin.SimpleListFilter):
    title = 'Нет роли'
    parameter_name = 'no_specific_role'

    def lookups(self, request, model_admin):
        roles = Role.objects.all()
        return [(role.id, role.name) for role in roles]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.exclude(roles__id=self.value())
        return queryset
