from django.db import models
from django.core.validators import MinLengthValidator

from users.constants import FIREBASE_UID_LENGTH


# Create your models here.
class User(models.Model):
    id=models.AutoField(primary_key=True)
    firebase_uid = models.CharField(max_length=FIREBASE_UID_LENGTH, unique=True, validators=[MinLengthValidator(FIREBASE_UID_LENGTH)]) #UID is 28 characters long
