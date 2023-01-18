import os

from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from categories.models import Category
from users.constants import FIREBASE_UID_LENGTH
from utils import create_random_string
from users.models import User


# Create your tests here.
class TestCategoriesModel(TestCase):

    def setUp(self):
        self.a_user = User.objects.create(firebase_uid=create_random_string(FIREBASE_UID_LENGTH))
        self.category_created = Category.objects.create(user=self.a_user, name='Education', material_ui_icon_name='School')

    def test_category_is_created_for_user(self):
        self.assertEqual(len(Category.categories_from_user(self.a_user)), 6)

    def test_category_from_user_is_deleted(self):
        self.category_created.delete()
        self.assertEqual(len(Category.categories_from_user(self.a_user)), 5)

    def test_created_category_is_not_static(self):
        self.assertFalse(self.category_created.static)

    def test_two_categories_with_same_name_should_not_be_created_for_a_user(self):
        with self.assertRaises(ValidationError):
            Category.objects.create(user=self.a_user, name='Education', material_ui_icon_name='Car')

    def test_category_dictionary_serialization(self):
        self.assertEqual(self.category_created.as_dict['id'], self.category_created.id)
        self.assertEqual(self.category_created.as_dict['name'],  'Education')
        self.assertEqual(self.category_created.as_dict['material_ui_icon_name'], 'School')
        self.assertFalse(self.category_created.as_dict['static'])
        self.assertEqual(self.category_created.as_dict['color'], self.category_created.color)
