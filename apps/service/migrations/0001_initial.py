# Generated by Django 3.2.19 on 2023-05-10 22:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('bot', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Donations',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(blank=True, max_length=100, verbose_name='Имя')),
                ('amount', models.CharField(blank=True, max_length=10, verbose_name='Количество')),
                ('currency', models.CharField(blank=True, max_length=30, verbose_name='Валюта')),
                ('message', models.CharField(blank=True, max_length=1000, verbose_name='Сообщение')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Дата')),
            ],
            options={
                'verbose_name': 'Донат',
                'verbose_name_plural': 'Донаты',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('name', models.CharField(max_length=50, primary_key=True, serialize=False, verbose_name='Имя')),
                ('value', models.CharField(default='', max_length=5000, null=True, verbose_name='Значение')),
                ('update_datetime', models.DateTimeField(auto_now=True, verbose_name='Дата создания')),
            ],
            options={
                'verbose_name': 'сервис',
                'verbose_name_plural': 'сервисы',
            },
        ),
        migrations.CreateModel(
            name='TaxiInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.JSONField(default=dict, verbose_name='Данные')),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Инфо о такси',
                'verbose_name_plural': 'Инфо о такси',
            },
        ),
        migrations.CreateModel(
            name='TimeZone',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, null=True, verbose_name='Временная зона UTC')),
            ],
            options={
                'verbose_name': 'таймзона',
                'verbose_name_plural': 'таймзоны',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Words',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('m1', models.CharField(max_length=500, null=True, verbose_name='Мужской')),
                ('f1', models.CharField(max_length=500, null=True, verbose_name='Женский')),
                ('n1', models.CharField(max_length=500, null=True, verbose_name='Средний')),
                ('mm', models.CharField(max_length=500, null=True, verbose_name='Множественный мужской')),
                ('fm', models.CharField(max_length=500, null=True, verbose_name='Множественный женский')),
                ('type',
                 models.CharField(choices=[('bad', 'Плохое'), ('good', 'Хорошее')], default='bad', max_length=10,
                                  verbose_name='Тип')),
            ],
            options={
                'verbose_name': 'Слово',
                'verbose_name_plural': 'Слова',
                'ordering': ['type', 'id'],
            },
        ),
        migrations.CreateModel(
            name='WakeOnLanUserData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Название')),
                ('ip', models.CharField(max_length=16, verbose_name='IP')),
                ('port', models.SmallIntegerField(verbose_name='Порт')),
                ('mac', models.CharField(max_length=17, verbose_name='MAC адрес')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.profile',
                                             verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'WOL устройство',
                'verbose_name_plural': 'WOL устройства',
            },
        ),
        migrations.CreateModel(
            name='Subscribe',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel_id', models.CharField(max_length=100, verbose_name='ID канала')),
                ('title', models.CharField(max_length=100, verbose_name='Название канала')),
                ('date', models.DateTimeField(blank=True, null=True, verbose_name='Дата последней публикации')),
                ('last_video_id',
                 models.CharField(blank=True, max_length=100, null=True, verbose_name='ID последнего видео')),
                ('service',
                 models.SmallIntegerField(blank=True, choices=[(1, 'YouTube'), (2, 'The Hole'), (3, 'WASD')], default=1,
                                          verbose_name='Сервис')),
                ('is_stream', models.BooleanField(blank=True, default=False, verbose_name='Флаг стрима')),
                ('last_stream_status',
                 models.BooleanField(blank=True, default=False, verbose_name='Последнее состояние стрима')),
                ('youtube_ignore_shorts',
                 models.BooleanField(blank=True, default=False, verbose_name='Игнорировать Youtube shorts')),
                ('message_thread_id',
                 models.IntegerField(blank=True, default=None, null=True, verbose_name='message_thread_id')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.user',
                                             verbose_name='Автор')),
                ('chat',
                 models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.chat',
                                   verbose_name='Чат')),
            ],
            options={
                'verbose_name': 'Подписка',
                'verbose_name_plural': 'Подписки',
                'ordering': ['title'],
            },
        ),
        migrations.CreateModel(
            name='Notify',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(blank=True, null=True, verbose_name='Дата напоминания')),
                ('crontab', models.CharField(blank=True, max_length=100, null=True, verbose_name='Crontab')),
                ('text', models.CharField(blank=True, default='', max_length=1000, verbose_name='Текст/команда')),
                ('text_for_filter', models.CharField(default='', max_length=1000, verbose_name='Текст для поиска')),
                ('repeat', models.BooleanField(default=False, verbose_name='Повторять')),
                ('mention_sender', models.BooleanField(default=True, verbose_name='Упоминать автора')),
                ('attachments', models.JSONField(blank=True, default=dict, verbose_name='Вложения')),
                ('message_thread_id',
                 models.IntegerField(blank=True, default=None, null=True, verbose_name='message_thread_id')),
                ('chat',
                 models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.chat',
                                   verbose_name='Чат')),
                ('user',
                 models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.user',
                                   verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'напоминание',
                'verbose_name_plural': 'напоминания',
                'ordering': ['user'],
            },
        ),
        migrations.CreateModel(
            name='Meme',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=1000, verbose_name='Название')),
                ('link', models.CharField(blank=True, default='', max_length=1000, null=True, verbose_name='Ссылка')),
                ('type', models.CharField(blank=True,
                                          choices=[('photo', 'Фото'), ('video', 'Видео'), ('audio', 'Аудио'),
                                                   ('doc', 'Документ'), ('link', 'Ссылка'), ('sticker', 'Стикер'),
                                                   ('gif', 'Гифка'), ('voice', 'Голосовое')], max_length=10,
                                          verbose_name='Тип')),
                ('uses', models.PositiveIntegerField(default=0, verbose_name='Использований')),
                ('approved', models.BooleanField(default=False, verbose_name='Разрешённый')),
                (
                    'tg_file_id',
                    models.CharField(blank=True, max_length=128, verbose_name='file_id стикера в телеграме')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bot.profile',
                                             verbose_name='Автор')),
            ],
            options={
                'verbose_name': 'мем',
                'verbose_name_plural': 'мемы',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='HoroscopeMeme',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=1000, verbose_name='Название')),
                ('link', models.CharField(blank=True, default='', max_length=1000, null=True, verbose_name='Ссылка')),
                ('type', models.CharField(blank=True,
                                          choices=[('photo', 'Фото'), ('video', 'Видео'), ('audio', 'Аудио'),
                                                   ('doc', 'Документ'), ('link', 'Ссылка'), ('sticker', 'Стикер'),
                                                   ('gif', 'Гифка'), ('voice', 'Голосовое')], max_length=10,
                                          verbose_name='Тип')),
                ('uses', models.PositiveIntegerField(default=0, verbose_name='Использований')),
                ('approved', models.BooleanField(default=False, verbose_name='Разрешённый')),
                (
                    'tg_file_id',
                    models.CharField(blank=True, max_length=128, verbose_name='file_id стикера в телеграме')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bot.profile',
                                             verbose_name='Автор')),
            ],
            options={
                'verbose_name': 'мем гороскопа',
                'verbose_name_plural': 'мемы гороскопа',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Horoscope',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('memes', models.ManyToManyField(to='service.HoroscopeMeme')),
            ],
            options={
                'verbose_name': 'Гороскоп',
                'verbose_name_plural': 'Гороскопы',
            },
        ),
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Название')),
                ('synonyms', models.CharField(max_length=300, verbose_name='Похожие названия')),
                ('lat', models.FloatField(null=True, verbose_name='Широта')),
                ('lon', models.FloatField(null=True, verbose_name='Долгота')),
                ('timezone', models.ForeignKey(default='', null=True, on_delete=django.db.models.deletion.SET_NULL,
                                               to='service.timezone', verbose_name='Временная зона UTC')),
            ],
            options={
                'verbose_name': 'город',
                'verbose_name_plural': 'города',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Название')),
                ('chat',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bot.chat', verbose_name='Чат')),
                ('users', models.ManyToManyField(blank=True, to='bot.Profile', verbose_name='Пользователи')),
            ],
            options={
                'verbose_name': 'Тег',
                'verbose_name_plural': 'Теги',
                'ordering': ['name'],
                'unique_together': {('name', 'chat')},
            },
        ),
    ]
