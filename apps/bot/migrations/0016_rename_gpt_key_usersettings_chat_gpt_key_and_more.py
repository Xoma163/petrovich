# Generated by Django 5.0.6 on 2024-05-27 08:58

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('bot', '0015_alter_bot_options_alter_chat_options_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='usersettings',
            old_name='gpt_key',
            new_name='chat_gpt_key',
        ),
        migrations.RenameField(
            model_name='usersettings',
            old_name='gpt_model',
            new_name='chat_gpt_model',
        ),
    ]
