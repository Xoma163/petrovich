# Generated by Django 3.2.1 on 2021-05-13 12:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='users',
            name='celebrate_bday',
            field=models.BooleanField(default=True, verbose_name='Поздравлять с Днём рождения'),
        ),
    ]