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

    @classmethod
    def current_budget_of(cls, user):
        current_budget = Budget.objects.filter(user=user, initial_date__lte=datetime.today().strftime('%Y-%m-%d'), final_date__gte=datetime.today().strftime('%Y-%m-%d'))

        if len(current_budget) == 0:
            return None
        else:
            return current_budget[0]

    @property
    def total_limit(self):
        details = LimitDetail.objects.filter(assigned_budget=self)
        total = sum([detail.limit for detail in details])
        return total

    @property
    def as_dict(self):
        return {
            'id': self.id,
            'initial_date': str(self.initial_date),
            'final_date': str(self.final_date),
            'details': [detail.as_dict for detail in Detail.from_budget(self)],
            'total_limit': float(self.total_limit),
            'total_spent': float(self.total_spent),
            'active': self.active,
            'has_finished': self.has_finished
        }

    @property
    def total_spent(self):
        total = sum([detail.total_spent for detail in LimitDetail.objects.filter(assigned_budget=self)])
        return total

    @property
    def editable(self):
        return not self.active and not self.has_began

    @property
    def has_began(self):
        return self.initial_date <= date.today()

    @property
    def has_finished(self):
        return self.has_began and self.final_date < date.today()

    def add_limit(self, category, limit):
        return LimitDetail.objects.create(category=category, value=limit, assigned_budget=self)

    def add_future_expense(self, category, value, name, expiration_date):
        return FutureExpenseDetail.objects.create(category=category, value=value, assigned_budget=self, expiration_date=expiration_date, name=name)

    def save(self, *args, update=False, **kwargs):
        self.full_clean()

        if self.final_date < self.initial_date:
            raise ValidationError("Budget initial date should be earlier than final date.")

        for budget in Budget.all_from_user(self.user):
            if not (update and budget.id == self.id):
                if (budget.initial_date <= self.final_date <= budget.final_date or budget.initial_date <= self.initial_date <= budget.final_date):
                    raise ValidationError("Budget is overlapping with another one.")

        super(Budget, self).save(*args, **kwargs)

    @property
    def active(self):
        return self.initial_date <= date.today() <= self.final_date

class Detail(models.Model):
    class Meta:
        abstract = True

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
        editable=True
    )

    assigned_budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
        editable=True
    )

    id = models.AutoField(primary_key=True)   

    value = models.DecimalField(
        max_digits=11,
        decimal_places=2,
        default=0.01,
        validators=[MinValueValidator(0.01)])  # Up to $100,000,000

    @classmethod
    def from_budget(cls, budget):
        return list(LimitDetail.objects.filter(assigned_budget=budget)) + list(FutureExpenseDetail.objects.filter(assigned_budget=budget))

class LimitDetail(Detail):
    class Meta:
        constraints = [models.UniqueConstraint(fields=['assigned_budget', 'category'], name='category repetition in limit detail is not allowed')]

    @property
    def as_dict(self):
        return {
            'category': self.category.as_dict,
            'limit': float(self.limit),
            'spent': float(self.total_spent)
        }
    
    @property
    def limit(self):
        return self.value

    @property
    def total_spent(self):
        expenses = Expense.objects.filter(
            user=self.assigned_budget.user,
            date__gte=self.assigned_budget.initial_date,
            date__lte=self.assigned_budget.final_date,
            category=self.category
        )

        total = sum([expense.value for expense in expenses])

        return total

class FutureExpenseDetail(Detail):
    name = models.CharField(max_length=50, null=True)
    expiration_date = models.DateField(validators=[], null=True)
    expended = models.BooleanField(default=False)

    @property
    def as_dict(self):
        return {
            'id': self.id,
            'category': self.category.as_dict,
            'value': float(self.value),
            'name': self.name,
            'expended': self.expended,
            'expiration_date': self.expiration_date
        }

    def should_be_notified(self):
        return (self.expiration_date - date.today()).days == 3 and not self.expended
    
    def save(self, *args, update=False, **kwargs):
        self.full_clean()

        if not (self.assigned_budget.initial_date <= self.expiration_date <= self.assigned_budget.final_date):
            raise ValidationError("Future Expense has to be between the budget dates.")

        super(FutureExpenseDetail, self).save(*args, **kwargs)