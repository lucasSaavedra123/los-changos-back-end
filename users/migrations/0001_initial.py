# Generated by Django 4.1 on 2022-10-02 01:43

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "firebase_uid",
                    models.CharField(
                        max_length=28,
                        unique=True,
                        validators=[django.core.validators.MinLengthValidator(28)],
                    ),
                ),
            ],
        ),
    ]
