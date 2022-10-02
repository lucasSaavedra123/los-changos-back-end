from django.db import models

from users.models import User

# Create your models here.
class Category(models.Model):
    id=models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    material_ui_icon_name = models.CharField(max_length=50)

    class Meta:
        abstract = True

class StaticCategory(Category):
    pass

class CustomCategory(Category):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
