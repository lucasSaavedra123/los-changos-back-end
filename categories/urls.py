from django.urls import path
from .views import category

urlpatterns = [
    path('', category)
]

from categories.models import Category

if Category.objects.all().count() == 0:
    Category.objects.create(name="Impuestos y Servicios", material_ui_icon_name="AccountBalance")
    Category.objects.create(name="Entretenimiento y Ocio", material_ui_icon_name="Casino")
    Category.objects.create(name="Hogar y Mercado", material_ui_icon_name="Home")
    Category.objects.create(name="Buen vivir/Antojos", material_ui_icon_name="EmojiEmotions")
    Category.objects.create(name="Electrodomesticos", material_ui_icon_name="Kitchen")
