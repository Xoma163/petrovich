# Generated by Django 5.0 on 2024-02-03 06:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('bot', '0001_initial'),
        ('games', '0001_initial'),
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
            name='gamer',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='profile',
                                       to='games.gamer', verbose_name='Игрок'),
        ),
        migrations.AddField(
            model_name='profile',
            name='groups',
            field=models.ManyToManyField(to='auth.group', verbose_name='Группы'),
        ),
        migrations.AddField(
            model_name='user',
            name='profile',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name='user', to='bot.profile', verbose_name='Профиль'),
        ),
        migrations.AddField(
            model_name='profile',
            name='settings',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='profile',
                                       to='bot.usersettings', verbose_name='Настройки'),
        ),
        migrations.AlterUniqueTogether(
            name='chat',
            unique_together={('chat_id', 'platform')},
        ),
        migrations.AlterUniqueTogether(
            name='user',
            unique_together={('user_id', 'platform')},
        ),
    ]
