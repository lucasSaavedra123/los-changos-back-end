# Generated by Django 4.0.1 on 2022-12-07 23:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_alias'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='alias',
            field=models.CharField(max_length=10, unique=True),
        ),
    ]
