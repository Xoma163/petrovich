# Generated by Django 5.0.2 on 2024-04-23 05:18

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bot', '0008_remove_usersettings_gpt_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersettings',
            name='gpt_model',
            field=models.CharField(blank=True, choices=[('gpt-4-turbo-2024-04-09', 'GPT-4 TURBO'), ('gpt-4', 'GPT-4'),
                                                        ('gpt-4-32k', 'GPT-4 32K'),
                                                        ('gpt-3.5-turbo-0125', 'GPT-3.5 TURBO 0125'),
                                                        ('gpt-3.5-turbo-instruct', 'GPT-3.5 TURBO INSTRUCT'),
                                                        ('gpt-4-0125-preview', 'GPT-4 0125'),
                                                        ('gpt-4-1106-preview', 'GPT-4 1106'),
                                                        ('gpt-4-vision-preview', 'GPT-4 VISION'),
                                                        ('gpt-3.5-turbo-1106', 'GPT-3.5 TURBO 1106'),
                                                        ('gpt-3.5-turbo-0613', 'GPT-3.5 TURBO 0613'),
                                                        ('gpt-3.5-turbo-16k-0613', 'GPT-3.5 TURBO 16K 0613'),
                                                        ('gpt-3.5-turbo-0301', 'GPT-3.5 TURBO 16K 0613')],
                                   max_length=64, verbose_name='модель GPT'),
        ),
    ]
