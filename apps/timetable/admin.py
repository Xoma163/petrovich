from django.contrib import admin

from apps.timetable import models


@admin.register(models.Group)
class GroupAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Teacher)
class TeacherAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Cabinet)
class CabinetAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Lesson)
class LessonAdmin(admin.ModelAdmin):
    pass
