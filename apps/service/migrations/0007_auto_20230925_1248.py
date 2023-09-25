# Generated by Django 3.2.20 on 2023-09-25 08:48

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('service', '0006_alter_subscribe_service'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subscribe',
            name='youtube_ignore_shorts',
        ),
        migrations.AlterField(
            model_name='subscribe',
            name='service',
            field=models.SmallIntegerField(blank=True,
                                           choices=[(1, 'YouTube'), (2, 'The Hole'), (4, 'VK'), (5, 'Premiere')],
                                           default=1, verbose_name='Сервис'),
        ),
    ]
