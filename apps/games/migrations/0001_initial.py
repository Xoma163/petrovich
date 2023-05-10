# Generated by Django 3.2.19 on 2023-05-10 22:19

import django.contrib.postgres.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('bot', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Gamer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('points', models.IntegerField(default=0, verbose_name='Очки ставок')),
                ('roulette_points', models.IntegerField(default=500, verbose_name='Очки рулетки')),
                ('bk_points', models.IntegerField(default=0, verbose_name='Очки быки и коровы')),
                ('wordle_points', models.IntegerField(default=0, verbose_name='Очки Wordle')),
                ('roulette_points_today', models.DateTimeField(auto_now_add=True, verbose_name='Дата получения очков')),
                ('profile', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.profile',
                                              verbose_name='Игрок')),
            ],
            options={
                'verbose_name': 'Игрок',
                'verbose_name_plural': 'Игроки',
                'ordering': ['profile'],
            },
        ),
        migrations.CreateModel(
            name='Wordle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('word', models.CharField(max_length=5)),
                ('steps', models.PositiveIntegerField(default=0, verbose_name='Количество попыток')),
                ('hypotheses', django.contrib.postgres.fields.ArrayField(
                    base_field=models.CharField(max_length=5, verbose_name='Гипотеза'), max_length=6, size=None,
                    verbose_name='Гипотезы')),
                ('message_id', models.IntegerField(blank=True, default=0, verbose_name='id первого сообщения')),
                ('chat', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.chat',
                                           verbose_name='Чат')),
                ('profile', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.profile',
                                              verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Сессия "Wordle"',
                'verbose_name_plural': 'Сессии "Wordle"',
                'ordering': ['chat'],
            },
        ),
        migrations.CreateModel(
            name='RouletteRate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rate_on', models.JSONField(blank=True, default=dict, verbose_name='Ставка')),
                ('rate', models.IntegerField(verbose_name='Размер ставки')),
                ('chat', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.chat',
                                           verbose_name='Чат')),
                ('gamer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='games.gamer',
                                            verbose_name='Игрок')),
            ],
            options={
                'verbose_name': 'Ставка рулеток',
                'verbose_name_plural': 'Ставки рулеток',
                'ordering': ['chat'],
            },
        ),
        migrations.CreateModel(
            name='Rate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rate', models.IntegerField(verbose_name='Ставка')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Дата')),
                ('random', models.BooleanField(default=False, verbose_name='Случайная')),
                ('chat', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.chat', verbose_name='Чат')),
                ('gamer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='games.gamer', verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Ставка',
                'verbose_name_plural': 'Ставки',
                'ordering': ['chat', 'date'],
            },
        ),
        migrations.CreateModel(
            name='PetrovichUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.BooleanField(default=True, verbose_name='Активность')),
                ('chat',
                 models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.chat',
                                   verbose_name='Чат')),
                ('profile', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.profile',
                                              verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Петрович игрок',
                'verbose_name_plural': 'Петрович игроки',
                'ordering': ['profile'],
            },
        ),
        migrations.CreateModel(
            name='PetrovichGames',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Дата')),
                ('chat',
                 models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.chat',
                                   verbose_name='Чат')),
                ('profile', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.profile',
                                              verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Петровича игра',
                'verbose_name_plural': 'Петрович игры',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='BullsAndCowsSession',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveIntegerField(verbose_name='Загаданное число')),
                ('steps', models.PositiveIntegerField(default=1, verbose_name='Количество попыток')),
                ('message_id', models.IntegerField(blank=True, default=0, verbose_name='id первого сообщения')),
                (
                'message_body', models.TextField(blank=True, verbose_name='Тело сообщения для игры в одном сообщении')),
                ('chat', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.chat',
                                           verbose_name='Чат')),
                ('profile', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bot.profile',
                                              verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Сессия "Быки и коровы"',
                'verbose_name_plural': 'Сессии "Быки и коровы"',
                'ordering': ['chat'],
            },
        ),
    ]
