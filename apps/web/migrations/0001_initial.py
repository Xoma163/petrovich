# Generated by Django 3.2.1 on 2021-07-12 08:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CalculatorProduct',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=127, verbose_name='Название')),
                ('count', models.PositiveIntegerField(blank=True, verbose_name='Количество')),
                ('uom', models.CharField(
                    choices=[('kg', 'кг'), ('g', 'г'), ('piece', 'шт'), ('jar', 'б'), ('packing', 'уп'),
                             ('liter', 'л')], default='piece', max_length=10, null=True,
                    verbose_name='Единица измерения')),
                ('is_bought', models.BooleanField(default=False, verbose_name='Куплено')),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, verbose_name='Цена')),
            ],
            options={
                'verbose_name': 'товар',
                'verbose_name_plural': 'товары',
            },
        ),
        migrations.CreateModel(
            name='CalculatorUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=127, verbose_name='Имя')),
            ],
            options={
                'verbose_name': 'пользователь',
                'verbose_name_plural': 'пользователи',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='CalculatorSession',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=127, verbose_name='Название')),
                ('products', models.ManyToManyField(blank=True, to='web.CalculatorProduct', verbose_name='Товары')),
                ('users', models.ManyToManyField(blank=True, to='web.CalculatorUser', verbose_name='Пользователи')),
            ],
            options={
                'verbose_name': 'сессия',
                'verbose_name_plural': 'сессии',
            },
        ),
        migrations.AddField(
            model_name='calculatorproduct',
            name='bought_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    to='web.calculatoruser', verbose_name='Кем куплено'),
        ),
    ]
