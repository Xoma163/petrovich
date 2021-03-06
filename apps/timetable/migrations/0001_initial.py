# Generated by Django 3.2.1 on 2021-05-05 06:45

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('bot', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cabinet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(help_text='***-* или другое', max_length=100, verbose_name='Номер кабинета')),
            ],
            options={
                'verbose_name': 'Кабинет',
                'verbose_name_plural': 'Кабинеты',
                'ordering': ['number'],
            },
        ),
        migrations.CreateModel(
            name='Discipline',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Полное название пары без сокращений', max_length=200, verbose_name='Название')),
                ('short_name', models.CharField(blank=True, help_text='Сокращенное название (если оставить пустым, то сгенерируется автоматически)', max_length=50, verbose_name='Название сокращённое')),
                ('bbb_link', models.TextField(blank=True, help_text='Бот будет слать этот текст когда наступит пара', verbose_name='Ссылка bbb')),
            ],
            options={
                'verbose_name': 'Предмет',
                'verbose_name_plural': 'Предметы',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveIntegerField(help_text='4 цифры', verbose_name='Номер группы')),
                ('title', models.CharField(blank=True, help_text='Бот будет менять заголовок конфы на это название группы', max_length=100, verbose_name='Название группы')),
                ('first_lesson_day', models.DateField(default=django.utils.timezone.now, help_text='Это поле нужно чтобы точно узнавать когда начинается первая неделя', verbose_name='Дата первой даты')),
                ('active', models.BooleanField(default=True, verbose_name='Обновлять расписание?')),
                ('conference', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bot.chat', verbose_name='Конфа')),
            ],
            options={
                'verbose_name': 'Группа',
                'verbose_name_plural': 'Группы',
                'ordering': ['number'],
            },
        ),
        migrations.CreateModel(
            name='Teacher',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Иванов И.И.', max_length=100, verbose_name='ФИО преподавателя')),
            ],
            options={
                'verbose_name': 'Преподаватель',
                'verbose_name_plural': 'Преподаватели',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lesson_number', models.CharField(choices=[('1', '1. 8:00-9:35'), ('2', '2. 9:45-11:20'), ('3', '3. 11:30-13:05'), ('4', '4. 13:30-15:05'), ('5', '5. 15:15-16:50'), ('6', '6. 17:00-18:35'), ('7', '7. 18:45-20:15'), ('8', '8. 20:25-21:55')], max_length=2, verbose_name='Номер пары')),
                ('lesson_type', models.CharField(choices=[('1', '🍏 Лекция'), ('2', '🍎 Практика'), ('3', '🍋 Лабораторная работа'), ('5', 'Курсовая'), ('4', 'Другое')], max_length=2, verbose_name='Тип пары')),
                ('week_number', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'), ('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'), ('15', '15'), ('16', '16'), ('17', '17'), ('18', '18'), ('19', '19'), ('20', '20')], max_length=2, verbose_name='Номер недели'), default=list, size=None, verbose_name='Номер недели')),
                ('day_of_week', models.CharField(choices=[('1', 'Понедельник'), ('2', 'Вторник'), ('3', 'Среда'), ('4', 'Четверг'), ('5', 'Пятница'), ('6', 'Суббота'), ('7', 'Воскресенье')], default='1', max_length=2, verbose_name='День недели')),
                ('subgroup', models.CharField(choices=[('0', 'Все'), ('1', '1'), ('2', '2')], default='0', max_length=2, verbose_name='Подгруппа')),
                ('cabinet', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='timetable.cabinet', verbose_name='Кабинет')),
                ('discipline', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='timetable.discipline', verbose_name='Предмет')),
                ('group', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='timetable.group', verbose_name='Группа')),
                ('teacher', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='timetable.teacher', verbose_name='Преподаватель')),
            ],
            options={
                'verbose_name': 'Пара',
                'verbose_name_plural': 'Пары',
                'ordering': ['day_of_week', 'lesson_number', 'subgroup'],
            },
        ),
    ]
