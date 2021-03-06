# Generated by Django 3.2.1 on 2021-05-05 06:45

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


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
            name='LaterMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(blank=True, max_length=300, verbose_name='Текст')),
                ('date', models.DateTimeField(verbose_name='Дата сообщения')),
                ('attachments', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, verbose_name='Вложения')),
                ('message_author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='message_author_latermessages', to='bot.users', verbose_name='Автор сообщения')),
                ('message_bot', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='bot.bot', verbose_name='Автор сообщения(бот)')),
            ],
            options={
                'verbose_name': 'Потом сообщение',
                'verbose_name_plural': 'Потом сообщения',
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
            name='Statistic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('command', models.CharField(max_length=20, verbose_name='Команда')),
                ('count_queries', models.IntegerField(default=0, verbose_name='Количество запросов')),
            ],
            options={
                'verbose_name': 'статистику',
                'verbose_name_plural': 'Статистика',
            },
        ),
        migrations.CreateModel(
            name='TaxiInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', django.contrib.postgres.fields.jsonb.JSONField(default=dict, verbose_name='Данные')),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
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
                ('type', models.CharField(choices=[('bad', 'Плохое'), ('good', 'Хорошее')], default='bad', max_length=10, verbose_name='Тип')),
            ],
            options={
                'verbose_name': 'Слово',
                'verbose_name_plural': 'Слова',
                'ordering': ['type', 'id'],
            },
        ),
        migrations.CreateModel(
            name='YoutubeSubscribe',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel_id', models.CharField(max_length=100, verbose_name='ID канала')),
                ('title', models.CharField(max_length=100, verbose_name='Название канала')),
                ('date', models.DateTimeField(verbose_name='Дата последней публикации')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.users', verbose_name='Автор')),
                ('chat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.chat', verbose_name='Чат')),
            ],
            options={
                'verbose_name': 'Подписка ютуба',
                'verbose_name_plural': 'Подписки ютуба',
                'ordering': ['title'],
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
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.users', verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'WOL устройство',
                'verbose_name_plural': 'WOL устройства',
            },
        ),
        migrations.CreateModel(
            name='QuoteBook',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(max_length=5000, verbose_name='Текст')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Дата')),
                ('chat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.chat', verbose_name='Чат')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.users', verbose_name='Автор')),
            ],
            options={
                'verbose_name': 'Цитата',
                'verbose_name_plural': 'Цитаты',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='Notify',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(verbose_name='Дата напоминания')),
                ('text', models.CharField(default='', max_length=1000, verbose_name='Текст/команда')),
                ('text_for_filter', models.CharField(default='', max_length=1000, verbose_name='Текст для поиска')),
                ('repeat', models.BooleanField(default=False, verbose_name='Повторять')),
                ('attachments', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, verbose_name='Вложения')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.users', verbose_name='Автор')),
                ('chat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.chat', verbose_name='Чат')),
            ],
            options={
                'verbose_name': 'напоминание',
                'verbose_name_plural': 'напоминания',
                'ordering': ['date'],
            },
        ),
        migrations.CreateModel(
            name='Meme',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=1000, verbose_name='Название')),
                ('link', models.CharField(blank=True, default='', max_length=1000, null=True, verbose_name='Ссылка')),
                ('type', models.CharField(blank=True, choices=[('photo', 'Фото'), ('video', 'Видео'), ('audio', 'Аудио'), ('doc', 'Документ')], max_length=5, verbose_name='Тип')),
                ('uses', models.PositiveIntegerField(default=0, verbose_name='Использований')),
                ('approved', models.BooleanField(default=False, verbose_name='Разрешённый')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bot.users', verbose_name='Автор')),
            ],
            options={
                'verbose_name': 'мем',
                'verbose_name_plural': 'мемы',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='LaterMessageSession',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(verbose_name='Дата сообщения')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.users', verbose_name='Автор')),
                ('later_messages', models.ManyToManyField(to='service.LaterMessage', verbose_name='Сообщения')),
            ],
            options={
                'verbose_name': 'Потом сообщение (сессия)',
                'verbose_name_plural': 'Потом сообщения (сессия)',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='Horoscope',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('memes', models.ManyToManyField(to='service.Meme')),
            ],
            options={
                'verbose_name': 'Гороскоп',
                'verbose_name_plural': 'Гороскопы',
            },
        ),
        migrations.CreateModel(
            name='Counter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=50, verbose_name='Имя')),
                ('count', models.IntegerField(default=0, verbose_name='Количество')),
                ('chat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.chat', verbose_name='Чат')),
            ],
            options={
                'verbose_name': 'счётчик',
                'verbose_name_plural': 'счётчики',
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
                ('timezone', models.ForeignKey(default='', null=True, on_delete=django.db.models.deletion.SET_NULL, to='service.timezone', verbose_name='Временная зона UTC')),
            ],
            options={
                'verbose_name': 'город',
                'verbose_name_plural': 'города',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Cat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='service/cats/', verbose_name='Изображение')),
                ('to_send', models.BooleanField(default=True, verbose_name='Ещё не было')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bot.users', verbose_name='Автор')),
            ],
            options={
                'verbose_name': 'кот',
                'verbose_name_plural': 'коты',
            },
        ),
    ]
