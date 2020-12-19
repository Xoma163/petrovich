# Generated by Django 3.0.8 on 2020-11-03 23:44

from django.db import migrations, models

import apps.bot.classes.Consts


class Migration(migrations.Migration):
    dependencies = [
        ('bot', '0007_auto_20201022_2250'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bot',
            name='platform',
            field=models.CharField(choices=[(apps.bot.classes.Consts.Platform['TG'], 'Telegram'),
                                            (apps.bot.classes.Consts.Platform['VK'], 'Vk'),
                                            (apps.bot.classes.Consts.Platform['API'], 'API')], max_length=3,
                                   verbose_name='Тип платформы'),
        ),
        migrations.AlterField(
            model_name='chat',
            name='platform',
            field=models.CharField(choices=[(apps.bot.classes.Consts.Platform['TG'], 'Telegram'),
                                            (apps.bot.classes.Consts.Platform['VK'], 'Vk'),
                                            (apps.bot.classes.Consts.Platform['API'], 'API')], max_length=3,
                                   verbose_name='Тип платформы'),
        ),
        migrations.AlterField(
            model_name='users',
            name='platform',
            field=models.CharField(choices=[(apps.bot.classes.Consts.Platform['TG'], 'Telegram'),
                                            (apps.bot.classes.Consts.Platform['VK'], 'Vk'),
                                            (apps.bot.classes.Consts.Platform['API'], 'API')], max_length=3,
                                   verbose_name='Тип платформы'),
        ),
    ]