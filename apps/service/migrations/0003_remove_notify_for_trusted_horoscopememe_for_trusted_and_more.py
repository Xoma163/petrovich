# Generated by Django 5.0 on 2024-02-03 07:02

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('service', '0002_notify_for_trusted'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notify',
            name='for_trusted',
        ),
        migrations.AddField(
            model_name='horoscopememe',
            name='for_trusted',
            field=models.BooleanField(default=False, verbose_name='Для доверенных пользователей'),
        ),
        migrations.AddField(
            model_name='meme',
            name='for_trusted',
            field=models.BooleanField(default=False, verbose_name='Для доверенных пользователей'),
        ),
    ]