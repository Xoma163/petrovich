# Generated by Django 3.2.19 on 2023-05-10 22:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('bot', '0001_initial'),
        ('service', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='city',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    to='service.city', verbose_name='Город'),
        ),
        migrations.AddField(
            model_name='profile',
            name='groups',
            field=models.ManyToManyField(to='auth.Group', verbose_name='Группы'),
        ),
        migrations.AddField(
            model_name='chat',
            name='admin',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    to='bot.profile', verbose_name='Админ'),
        ),
    ]
