# Generated by Django 5.0.7 on 2024-08-19 21:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('service', '0020_remove_subscribe_save_to_plex_subscribe_save_to_disk_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscribe',
            name='high_resolution',
            field=models.BooleanField(default=False, verbose_name='Присылать в высоком разрешении'),
        ),
    ]
