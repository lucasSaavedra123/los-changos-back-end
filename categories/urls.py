from django.urls import path
from .models import StaticCategory

urlpatterns = []

if StaticCategory.objects.all().count() == 0:
    StaticCategory.objects.create(name="Impuestos y Servicios", material_ui_icon_name="AccountBalance")
    StaticCategory.objects.create(name="Entretenimiento y Ocio", material_ui_icon_name="Casino")
    StaticCategory.objects.create(name="Hogar y Mercado", material_ui_icon_name="Home")
    StaticCategory.objects.create(name="Buen vivir/Antojos", material_ui_icon_name="EmojiEmotions")
    StaticCategory.objects.create(name="Electrodomesticos", material_ui_icon_name="Kitchen")
