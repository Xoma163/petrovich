# Generated by Django 5.0.7 on 2024-07-15 12:27

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('bot', '0018_remove_profile_gamer'),
        ('games', '0008_remove_rate_chat_remove_rate_gamer_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Gamer',
        ),
    ]