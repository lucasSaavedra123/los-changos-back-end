# Generated by Django 4.0.1 on 2022-11-08 17:22

import budgets.models
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
        ('categories', '0002_category_color'),
    ]

    operations = [
        migrations.CreateModel(
            name='Budget',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('initial_date', models.DateField()),
                ('final_date', models.DateField(validators=[budgets.models.validate_date_is_not_in_the_past])),
                ('user', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
        ),
        migrations.CreateModel(
            name='Detail',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('limit', models.DecimalField(decimal_places=2, default=0.01, max_digits=11, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('assigned_budget', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='budgets.budget')),
                ('category', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='categories.category')),
            ],
        ),
        migrations.AddConstraint(
            model_name='detail',
            constraint=models.UniqueConstraint(fields=('assigned_budget', 'category'), name='category repetition is not available'),
        ),
    ]
