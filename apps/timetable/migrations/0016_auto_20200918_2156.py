# Generated by Django 3.0.8 on 2020-09-18 17:56

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('timetable', '0015_group_first_lesson_day'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='first_lesson_day',
            field=models.DateField(default=django.utils.timezone.now,
                                   help_text='Это поле нужно чтобы точно узнавать когда начинается первая неделя',
                                   verbose_name='Дата первой даты'),
        ),
    ]