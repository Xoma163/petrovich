# Generated by Django 5.1.6 on 2025-04-17 07:11

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bot', '0025_chatsettings_time_conversion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profilesettings',
            name='chat_gpt_model',
            field=models.CharField(blank=True,
                                   choices=[('o1', 'o1'), ('o1-pro', 'o1 pro'), ('o1-mini', 'o1 mini'), ('o3', 'o3'),
                                            ('o3-mini', 'o3 mini'), ('o4-mini', 'o4 mini'), ('gpt-4.1', 'GPT-4.1'),
                                            ('gpt-4.1-mini', 'GPT-4.1 MINI'), ('gpt-4.1-nano', 'GPT-4.1 NANO'),
                                            ('gpt-4o', 'GPT-4o'), ('gpt-4o-mini', 'GPT-4o MINI'), ('gpt-4', 'GPT-4'),
                                            ('gpt-4-turbo', 'GPT-4 TURBO'), ('gpt-4-32k', 'GPT-4 32K'),
                                            ('gpt-4.5-preview', 'GPT-4.5'),
                                            ('gpt-3.5-turbo-0125', 'GPT-3.5 TURBO 0125'),
                                            ('gpt-3.5-turbo-1106', 'GPT-3.5 TURBO 1106'),
                                            ('gpt-3.5-turbo-0613', 'GPT-3.5 TURBO 0613'),
                                            ('gpt-3.5-turbo-16k-0613', 'GPT-3.5 TURBO 16K 0613'),
                                            ('gpt-3.5-turbo-0301', 'GPT-3.5 TURBO 16K 0613')], max_length=64,
                                   verbose_name='модель GPT'),
        ),
    ]
