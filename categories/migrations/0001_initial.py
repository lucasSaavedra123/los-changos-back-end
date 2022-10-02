# Generated by Django 4.0.1 on 2022-10-02 21:00

from django.db import migrations, models
import django.db.models.deletion

def populate_static_categories(apps, schema_editor):
    Category = apps.get_model('categories', 'Category')

    if Category.objects.filter(user=None).count() == 0:
        Category.objects.create(name="Impuestos y Servicios", material_ui_icon_name="AccountBalance")
        Category.objects.create(name="Entretenimiento y Ocio", material_ui_icon_name="Casino")
        Category.objects.create(name="Hogar y Mercado", material_ui_icon_name="Home")
        Category.objects.create(name="Buen vivir/Antojos", material_ui_icon_name="EmojiEmotions")
        Category.objects.create(name="Electrodomesticos", material_ui_icon_name="Kitchen")


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(default='Categoria Personalizada', max_length=50)),
                ('material_ui_icon_name', models.CharField(default='Paid', max_length=50)),
                ('user', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
        ),
        migrations.RunPython(populate_static_categories)
    ]
