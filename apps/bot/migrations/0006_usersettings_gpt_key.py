# Generated by Django 5.0.2 on 2024-04-19 04:10

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bot', '0005_usersettings_is_newsletter_subscriber'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersettings',
            name='gpt_key',
            field=models.CharField(blank=True, max_length=64, verbose_name='Ключ GPT'),
        ),
    ]