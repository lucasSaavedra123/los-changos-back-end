from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

from users.models import User
from categories.models import Category
from datetime import date
from datetime import datetime

def validate_date_is_not_in_the_future(value):
    today = date.today()
    if value > today:
        raise ValidationError('Expense date cannot be in the future.')

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

    initial_date = models.DateField(validators=[validate_date_is_not_in_the_future])
    final_date = models.DateField(validators=[validate_date_is_not_in_the_future])

    @property
    def total_limit(self):
        details = Detail.objects.filter(assigned_budget=self)
        total = 0

        for detail in details:
            total += detail.limit

        return total

    def add_detail(self, category, limit):
        Detail.objects.create(category=category, limit=limit, assigned_budget=self)

    """
    def save(self, *args, update=False, **kwargs):
        self.name = self.name.lower()
        user_categories = Category.categories_from_user(self.user)

        if not update:
            for category in user_categories:
                if category.name == self.name:
                    raise ValidationError(
                        "User cannot create another repeated category")

        self.color = create_random_color_string()

        self.full_clean()
        super(Category, self).save(*args, **kwargs)
    """

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
