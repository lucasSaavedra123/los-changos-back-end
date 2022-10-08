# Generated by Django 4.0.1 on 2022-10-08 19:38

import django.core.validators
from django.db import migrations, models
import expenses.models


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0002_alter_expense_value'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expense',
            name='date',
            field=models.DateField(validators=[expenses.models.validate_date_is_not_in_the_future]),
        ),
        migrations.AlterField(
            model_name='expense',
            name='value',
            field=models.DecimalField(decimal_places=3, default=0.01, max_digits=11, validators=[django.core.validators.MinValueValidator(0.01)]),
        ),
    ]
