from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator

from users.constants import FIREBASE_UID_LENGTH


# Create your models here.
class User(models.Model):
    id=models.AutoField(primary_key=True)
    firebase_uid = models.CharField(
        max_length=FIREBASE_UID_LENGTH,
        unique=True,
        validators=[MinLengthValidator(FIREBASE_UID_LENGTH)],
        null=False
    ) # UID is 28 characters long
    email = models.CharField(
        max_length=320,
        unique=True,
        validators=[MaxLengthValidator(320)],
        null=False
    ) # Maximum Email length is here https://www.lifewire.com/is-email-address-length-limited-1171110
