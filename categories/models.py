from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from users.models import User
from utils import create_random_color_string


# Create your models here.
class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        default="Categoria Personalizada",
        editable=True)
    
    material_ui_icon_name = models.CharField(
        max_length=50,
        default="Paid",
        editable=True)

    color = models.CharField(
        max_length=50,
        default=None,
        editable=False,
        null=True
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
        editable=True
    )

    @classmethod
    def static_categories(cls):
        return cls.objects.filter(user=None)

    @classmethod
    def create_category_for_user(cls, user, **kwargs):
        cls.objects.create(user=user, **kwargs)

    @classmethod
    def categories_from_user(cls, user):
        static_categories = cls.static_categories()
        user_created_categories = cls.objects.filter(user=user)
        return static_categories.union(user_created_categories)

    @property
    def static(self):
        return self.user == None

    @property
    def as_dict(self):
        return {
            'id': self.id,
            'material_ui_icon_name': self.material_ui_icon_name,
            'static': self.static,
            'name': self.name.title(),
            'color': self.color
        }

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
