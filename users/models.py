from django.db import models
from django.core.validators import MinLengthValidator

from users.constants import FIREBASE_UID_LENGTH


# Create your models here.
class User(models.Model):
    id=models.AutoField(primary_key=True)
    firebase_uid = models.CharField(
        max_length=FIREBASE_UID_LENGTH,
        unique=True,
        validators=[MinLengthValidator(FIREBASE_UID_LENGTH)]
    ) # UID is 28 characters long
    alias = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=10)
    apellido = models.CharField(max_length=10)



    @property
    def as_dict(self):
        return {
            'id': self.id,
            'firebase_uid': self.firebase_uid,
            'alias': self.alias,
            'nombre': self.nombre,
            'apellido': self.apellido,
        }
