# Generated by Django 3.0.8 on 2020-12-19 09:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0010_auto_20201219_1353'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='need_meme',
            field=models.BooleanField(default=False, verbose_name='Слать мемы'),
        ),
    ]