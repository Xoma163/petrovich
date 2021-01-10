# Generated by Django 3.0.8 on 2021-01-10 16:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0009_auto_20210110_1653'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calculatorproduct',
            name='uom',
            field=models.CharField(choices=[('kg', 'кг'), ('g', 'г'), ('piece', 'шт'), ('jar', 'б'), ('packing', 'уп'), ('liter', 'л')], default='piece', max_length=10, null=True, verbose_name='Единица измерения'),
        ),
    ]
