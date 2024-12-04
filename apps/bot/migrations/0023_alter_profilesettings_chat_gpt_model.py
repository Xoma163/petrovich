# Generated by Django 5.1 on 2024-12-04 18:20

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bot', '0022_rename_usersettings_profilesettings'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profilesettings',
            name='chat_gpt_model',
            field=models.CharField(blank=True, choices=[('o1-preview', 'GPT-o1 preview'), ('o1-mini', 'GPT-o1 mini'),
                                                        ('gpt-4o-mini', 'GPT-4 OMNI MINI'), ('gpt-4o', 'GPT-4 OMNI'),
                                                        ('gpt-4-turbo', 'GPT-4 TURBO'), ('gpt-4', 'GPT-4'),
                                                        ('gpt-4-32k', 'GPT-4 32K'),
                                                        ('gpt-3.5-turbo-0125', 'GPT-3.5 TURBO 0125'),
                                                        ('gpt-3.5-turbo-1106', 'GPT-3.5 TURBO 1106'),
                                                        ('gpt-3.5-turbo-0613', 'GPT-3.5 TURBO 0613'),
                                                        ('gpt-3.5-turbo-16k-0613', 'GPT-3.5 TURBO 16K 0613'),
                                                        ('gpt-3.5-turbo-0301', 'GPT-3.5 TURBO 16K 0613')],
                                   max_length=64, verbose_name='модель GPT'),
        ),
    ]