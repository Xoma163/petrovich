# Generated by Django 3.2.19 on 2023-05-10 23:48

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('service', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='horoscopememe',
            name='tg_file_id',
            field=models.CharField(blank=True, max_length=128, verbose_name='file_id в tg'),
        ),
        migrations.AlterField(
            model_name='meme',
            name='tg_file_id',
            field=models.CharField(blank=True, max_length=128, verbose_name='file_id в tg'),
        ),
    ]
