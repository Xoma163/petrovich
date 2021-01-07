# Register your models here.
from django.contrib import admin

from apps.web.models import CalculatorUser, CalculatorProduct, CalculatorSession


@admin.register(CalculatorUser)
class CalculatorUserAdmin(admin.ModelAdmin):
    pass


@admin.register(CalculatorProduct)
class CalculatorProductAdmin(admin.ModelAdmin):
    pass


@admin.register(CalculatorSession)
class CalculatorSessionAdmin(admin.ModelAdmin):
    pass
