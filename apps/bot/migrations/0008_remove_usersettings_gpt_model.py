# Generated by Django 5.0.2 on 2024-04-23 05:17

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('bot', '0007_usersettings_gpt_model'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usersettings',
            name='gpt_model',
        ),
    ]