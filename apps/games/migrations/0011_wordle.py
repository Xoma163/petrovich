# Generated by Django 3.2.13 on 2022-10-16 17:12

import django.contrib.postgres.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bot', '0015_chat_use_swear'),
        ('games', '0010_bullsandcowssession_message_body'),
    ]

    operations = [
        migrations.CreateModel(
            name='Wordle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('word', models.CharField(max_length=5)),
                ('steps', models.PositiveIntegerField(default=1, verbose_name='Количество попыток')),
                ('hypotheses', django.contrib.postgres.fields.ArrayField(
                    base_field=models.CharField(max_length=5, verbose_name='Гипотеза'), max_length=6, size=None,
                    verbose_name='Гипотезы')),
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
    ]