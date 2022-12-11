# Generated by Django 4.0.1 on 2022-12-11 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_user_alias'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='alias',
        ),
        migrations.AddField(
            model_name='user',
            name='apellido',
            field=models.CharField(default=1, max_length=10),
            preserve_default=False,
        ),
    ]
