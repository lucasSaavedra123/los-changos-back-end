# Generated by Django 4.0.1 on 2022-12-05 17:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0002_category_color'),
        ('expenses', '0006_rename_isexpense_expense_expense'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expense',
            name='category',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, to='categories.category'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='expense',
            name='expense',
            field=models.CharField(default='true', max_length=5),
        ),
    ]
