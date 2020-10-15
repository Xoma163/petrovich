from django.contrib import admin

from apps.timetable import models
from apps.timetable.actions import clone
from apps.timetable.forms import LessonForm


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
    actions = [clone]
    form = LessonForm
    list_filter = (
    'group', 'subgroup', 'day_of_week', 'lesson_number', 'lesson_type', 'discipline', 'teacher', 'cabinet',)
