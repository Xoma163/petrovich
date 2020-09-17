from django import forms
from django.forms import TypedMultipleChoiceField

from apps.timetable.models import Lesson


class LessonForm(forms.ModelForm):
    week_number = TypedMultipleChoiceField(choices=Lesson.WEEK_NUMBERS)
