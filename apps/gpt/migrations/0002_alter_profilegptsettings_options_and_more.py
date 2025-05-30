# Generated by Django 5.1.6 on 2025-05-11 13:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bot', '0002_initial'),
        ('gpt', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='profilegptsettings',
            options={'verbose_name': 'Настройка профиля GPT', 'verbose_name_plural': 'Настройки профиля GPT'},
        ),
        migrations.RemoveConstraint(
            model_name='completionsmodel',
            name='unique_name_completion_model',
        ),
        migrations.RemoveConstraint(
            model_name='imagedrawmodel',
            name='unique_name_width_height_quality_img_draw',
        ),
        migrations.RemoveConstraint(
            model_name='imageeditmodel',
            name='unique_name_width_height_image_edit',
        ),
        migrations.RemoveConstraint(
            model_name='visionmodel',
            name='unique_name_vision_model',
        ),
        migrations.RemoveConstraint(
            model_name='voicerecognitionmodel',
            name='unique_name_voice_recognition_model',
        ),
        migrations.AlterField(
            model_name='completionsmodel',
            name='is_default',
            field=models.BooleanField(default=False, verbose_name='Модель по умолчанию'),
        ),
        migrations.AlterField(
            model_name='imagedrawmodel',
            name='is_default',
            field=models.BooleanField(default=False, verbose_name='Модель по умолчанию'),
        ),
        migrations.AlterField(
            model_name='imageeditmodel',
            name='is_default',
            field=models.BooleanField(default=False, verbose_name='Модель по умолчанию'),
        ),
        migrations.AlterField(
            model_name='visionmodel',
            name='is_default',
            field=models.BooleanField(default=False, verbose_name='Модель по умолчанию'),
        ),
        migrations.AlterField(
            model_name='voicerecognitionmodel',
            name='is_default',
            field=models.BooleanField(default=False, verbose_name='Модель по умолчанию'),
        ),
        migrations.AlterUniqueTogether(
            name='profilegptsettings',
            unique_together={('profile', 'provider')},
        ),
        migrations.AddConstraint(
            model_name='completionsmodel',
            constraint=models.UniqueConstraint(fields=('name', 'provider'), name='unique_name_completion_model'),
        ),
        migrations.AddConstraint(
            model_name='imagedrawmodel',
            constraint=models.UniqueConstraint(fields=('name', 'width', 'height', 'quality', 'provider'),
                                               name='unique_name_width_height_quality_img_draw'),
        ),
        migrations.AddConstraint(
            model_name='imageeditmodel',
            constraint=models.UniqueConstraint(fields=('name', 'width', 'height', 'provider'),
                                               name='unique_name_width_height_image_edit'),
        ),
        migrations.AddConstraint(
            model_name='visionmodel',
            constraint=models.UniqueConstraint(fields=('name', 'provider'), name='unique_name_vision_model'),
        ),
        migrations.AddConstraint(
            model_name='voicerecognitionmodel',
            constraint=models.UniqueConstraint(fields=('name', 'provider'), name='unique_name_voice_recognition_model'),
        ),
    ]
