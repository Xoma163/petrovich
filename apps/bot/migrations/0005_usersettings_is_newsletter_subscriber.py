# Generated by Django 5.0.2 on 2024-02-28 15:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bot', '0004_usersettings_use_mention'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersettings',
            name='is_newsletter_subscriber',
            field=models.BooleanField(default=False, verbose_name='Подписчик новостной рассылки'),
        ),
    ]
