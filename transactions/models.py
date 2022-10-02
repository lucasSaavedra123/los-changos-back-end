from django.db import models
from django.core.validators import MinValueValidator
from categories.models import Category

from users.models import User


# Create your models here.
class Transaction(models.Model):
    id=models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    value = models.DecimalField(max_digits=11, decimal_places=2, default=0.01, validators=[MinValueValidator(0.01)]) #Up to $100,000,000
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
