# Generated by Django 3.0.8 on 2020-10-22 18:50

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('timetable', '0018_lesson_subgroup'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='lesson',
            options={'ordering': ['day_of_week', 'lesson_number', 'subgroup'], 'verbose_name': 'Пара',
                     'verbose_name_plural': 'Пары'},
        ),
        migrations.AlterField(
            model_name='group',
            name='title',
            field=models.CharField(blank=True, help_text='Бот будет менять заголовок конфы на это название группы',
                                   max_length=100, verbose_name='Название группы'),
        ),
    ]
