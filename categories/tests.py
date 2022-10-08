from django.test import TestCase
from categories.models import Category
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from rest_framework import status
from utils import create_random_string
from users.models import User
from django.core.exceptions import ValidationError


# Create your tests here.
class TestCategoriesModel(TestCase):

    def setUp(self):
        self.a_user = User.objects.create(firebase_uid=create_random_string(28))
        self.category_created = Category.objects.create(user=self.a_user, name="Education", material_ui_icon_name="School")

    def test_category_is_created_for_user(self):
        self.assertEqual(len(Category.categories_from_user(self.a_user)), 6)

    def test_category_from_user_is_deleted(self):
        self.category_created.delete()
        self.assertEqual(len(Category.categories_from_user(self.a_user)), 5)

    def test_two_categories_with_same_name_should_not_be_created_for_a_user(self):
        with self.assertRaises(ValidationError):
            Category.objects.create(user=self.a_user, name="eDucatioN", material_ui_icon_name="Car")


"""
class TestCategoriesView(APITestCase):
    pass
"""