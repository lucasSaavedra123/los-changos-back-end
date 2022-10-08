from django.test import TestCase
from categories.models import Category
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from rest_framework import status
from users.constants import FIREBASE_UID_LENGTH
from utils import create_random_string
from users.models import User
from django.core.exceptions import ValidationError


# Create your tests here.
class TestCategoriesModel(TestCase):

    def setUp(self):
        self.a_user = User.objects.create(firebase_uid=create_random_string(FIREBASE_UID_LENGTH))
        self.category_created = Category.objects.create(user=self.a_user, name="Education", material_ui_icon_name="School")

    def test_category_is_created_for_user(self):
        self.assertEqual(len(Category.categories_from_user(self.a_user)), 6)

    def test_category_from_user_is_deleted(self):
        self.category_created.delete()
        self.assertEqual(len(Category.categories_from_user(self.a_user)), 5)

    def test_created_category_is_not_static(self):
        self.assertFalse(self.category_created.static)

    def test_two_categories_with_same_name_should_not_be_created_for_a_user(self):
        with self.assertRaises(ValidationError):
            Category.objects.create(user=self.a_user, name="eDucatioN", material_ui_icon_name="Car")

    def test_category_dictionary_serialization(self):
        self.assertDictEqual(self.category_created.as_dict,{
                "id": self.category_created.id,
                "name": "education",
                "material_ui_icon_name": "School",
                "static": False
            })

"""
class TestCategoriesView(APITestCase):
    pass
"""