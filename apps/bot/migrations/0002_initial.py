# Generated by Django 3.2.1 on 2021-05-05 06:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('service', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('bot', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='users',
            name='city',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='service.city', verbose_name='Город'),
        ),
        migrations.AddField(
            model_name='users',
            name='groups',
            field=models.ManyToManyField(to='auth.Group', verbose_name='Группы'),
        ),
        migrations.AddField(
            model_name='users',
            name='send_notify_to',
            field=models.ManyToManyField(blank=True, related_name='_bot_users_send_notify_to_+', to='bot.Users', verbose_name='Отправлять уведомления'),
        ),
        migrations.AddField(
            model_name='chat',
            name='admin',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='bot.users', verbose_name='Админ'),
        ),
    ]
