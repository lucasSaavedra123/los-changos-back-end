from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from categories.models import Category
from datetime import date
from users.models import User
from datetime import datetime


def validate_date_is_not_in_the_future(value):
    today = date.today()
    if value > today:
        raise ValidationError('Expense date cannot be in the future.')

# Create your models here.


class Expense(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(validators=[validate_date_is_not_in_the_future])
    value = models.DecimalField(
        max_digits=11,
        decimal_places=2,
        default=0.01,
        validators=[MinValueValidator(0.01)])  # Up to $100,000,000
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    @classmethod
    def create_expense_for_user(cls, user, **kwargs):
        cls.objects.create(user=user, **kwargs)

    @classmethod
    def expenses_from_user(cls, user):
        return cls.objects.filter(user=user)

    @classmethod
    def filter_within_timeline_from_user(cls, user, first_date, last_date):
        return cls.objects.filter(user=user, date__gte=first_date, date__lte=last_date)

    @classmethod
    def filter_by_category_within_timeline_from_user(cls, user, first_date, last_date, selected_category):
        return cls.objects.filter(user=user, date__gte=first_date, date__lte=last_date, category=selected_category)

    @property
    def as_dict(self):
        return {
            'id': self.id,
            'date': str(self.date),
            'category': self.category.as_dict,
            'value': float(self.value),
            'name': self.name
        }

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
