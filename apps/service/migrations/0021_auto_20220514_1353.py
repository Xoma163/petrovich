# Generated by Django 3.2.12 on 2022-05-14 09:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('service', '0020_auto_20220514_1353'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscribe',
            name='last_video_id',
            field=models.CharField(max_length=100, null=True, verbose_name='ID последнего видео'),
        ),
        migrations.AddField(
            model_name='subscribe',
            name='service',
            field=models.SmallIntegerField(blank=True, choices=[(1, 'Ютуб'), (2, 'The hole')], default=1,
                                           verbose_name='Сервис'),
        ),
    ]
