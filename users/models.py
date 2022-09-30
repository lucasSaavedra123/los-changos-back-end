from django.db import models
from django.core.validators import MinLengthValidator

# Create your models here.
class User(models.Model):
    id=models.AutoField(primary_key=True)
    firebase_id = models.CharField(max_length=28, unique=True, validators=[MinLengthValidator(28)])
