from django.db import models

# Create your models here.
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from categories.models import Category
from datetime import date
from users.models import User
from expenses.models import Expense
from datetime import datetime
import requests

def validate_date_is_not_in_the_future(value):
    today = date.today()
    if value > today:
        raise ValidationError('Expense date cannot be in the future.')

# Create your models here.


class SharedExpense(Expense):
    userToShare= models.ForeignKey(User, on_delete=models.CASCADE, related_name='userToShare')
    userToShareFlag= models.BooleanField(default=True)

    @classmethod
    def create_expense_for_user(cls, user, **kwargs):
        cls.objects.create(user=user, **kwargs)

    @classmethod
    def expenses_from_user(cls, user):
        return cls.objects.order_by('-date').filter(user=user)
    
    @classmethod
    def expenses_user_made_with_me(cls, user):
        return cls.objects.order_by('-date').filter(userToShare=user)

    @classmethod
    def filter_within_timeline_from_user(cls, user, first_date, last_date):
        return cls.objects.order_by('-date').filter(user=user, date__gte=first_date, date__lte=last_date)

    @classmethod
    def filter_within_timeline_from_otherUser(cls, user, first_date, last_date):
        return cls.objects.order_by('-date').filter(userToShare=user, date__gte=first_date, date__lte=last_date)

    @classmethod
    def filter_by_category_within_timeline_from_user(cls, user, first_date, last_date, selected_category):
        return cls.objects.order_by('-date').filter(user=user, date__gte=first_date, date__lte=last_date, category=selected_category)
    
    @classmethod
    def filter_by_category_within_timeline_from_otherUser(cls, user, first_date, last_date, selected_category):
        return cls.objects.order_by('-date').filter(userToShare=user, date__gte=first_date, date__lte=last_date, category=selected_category)

   
   
    @property
    def as_dict(self):
        return {
            'id': self.id,
            'date': str(self.date),
            'category': self.category.as_dict,
            'value': float(self.value),
            'name': self.name,
            'userToShare': self.userToShare.as_dict,
            'userToShareFlag': self.userToShareFlag
    }
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
