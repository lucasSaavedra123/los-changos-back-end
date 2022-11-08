from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

from users.models import User
from categories.models import Category
from expenses.models import Expense
from datetime import date
from datetime import datetime

def validate_date_is_not_in_the_past(value):
    today = date.today()
    if value < today:
        raise ValidationError('Budget date cannot be in the past.')

# Create your models here.
class Budget(models.Model):
    id = models.AutoField(primary_key=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
        editable=True
    )

    initial_date = models.DateField(validators=[])
    final_date = models.DateField(validators=[validate_date_is_not_in_the_past])

    @classmethod
    def all_from_user(cls, user):
        return Budget.objects.filter(user=user)

    @property
    def total_limit(self):
        details = Detail.objects.filter(assigned_budget=self)
        total = 0

        for detail in details:
            total += detail.limit

        return total

    @property
    def as_dict(self):
        return {
            'id': self.id,
            'initial_date': str(self.initial_date),
            'final_date': str(self.final_date),
            'details': [detail.as_dict for detail in Detail.from_budget(self)],
            'total_limit': float(self.total_limit),
            'total_spent': float(self.total_spent)
        }

    @property
    def total_spent(self):
        total = 0

        for detail in Detail.objects.filter(assigned_budget=self):
            total += detail.total_spent

        return total

    def add_detail(self, category, limit):
        return Detail.objects.create(category=category, limit=limit, assigned_budget=self)

    def save(self, *args, update=False, **kwargs):
        self.full_clean()

        if self.final_date < self.initial_date:
            raise ValidationError("Budget initial date should be earlier than final date.")

        if not update:
            for budget in Budget.all_from_user(self.user):
                if (budget.initial_date <= self.final_date <= budget.final_date or budget.initial_date <= self.initial_date <= budget.final_date):
                    raise ValidationError("Budget is overlapping with another one.")

        super(Budget, self).save(*args, **kwargs)

class Detail(models.Model):
    class Meta:
        constraints = [models.UniqueConstraint(fields=['assigned_budget', 'category'], name='category repetition is not available')]

    id = models.AutoField(primary_key=True)   

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
        editable=True
    )

    limit = models.DecimalField(
        max_digits=11,
        decimal_places=2,
        default=0.01,
        validators=[MinValueValidator(0.01)])  # Up to $100,000,000
    
    assigned_budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
        editable=True
    )

    @classmethod
    def from_budget(cls, budget):
        return cls.objects.filter(assigned_budget=budget)

    @property
    def as_dict(self):
        return {
            'id': self.id,
            'category': self.category.as_dict,
            'limit': float(self.limit),
            'spent': float(self.total_spent)
        }

    @property
    def total_spent(self):
        expenses = Expense.objects.filter(
            user=self.assigned_budget.user,
            date__gte=self.assigned_budget.initial_date,
            date__lte=self.assigned_budget.final_date,
            category=self.category
        )

        total = 0

        for expense in expenses:
            total += expense.value

        return total
