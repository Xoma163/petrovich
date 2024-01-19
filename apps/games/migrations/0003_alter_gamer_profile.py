# Generated by Django 5.0 on 2024-01-19 13:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bot', '0014_remove_usersettings_recognize_voice_and_more'),
        ('games', '0002_alter_gamer_profile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gamer',
            name='profile',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='gamer',
                                       to='bot.profile', verbose_name='Игрок'),
        ),
    ]
