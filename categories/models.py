from django.db import models

from users.models import User


# Create your models here.
class Category(models.Model):
    id=models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    material_ui_icon_name = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None, null=True, blank=True, db_constraint=False)
