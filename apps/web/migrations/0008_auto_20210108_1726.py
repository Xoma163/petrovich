# Generated by Django 3.0.8 on 2021-01-08 13:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0007_auto_20210107_0632'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='calculatorproduct',
            name='Кем куплено',
        ),
        migrations.AddField(
            model_name='calculatorproduct',
            name='bought_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='web.CalculatorUser', verbose_name='Кем куплено'),
        ),
    ]
