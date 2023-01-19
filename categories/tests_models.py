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

from random import randint

# Create your tests here.
class TestCategoriesModel(TestCase):

    def setUp(self):
        self.a_user = User.objects.create(firebase_uid=create_random_string(FIREBASE_UID_LENGTH))

    def test_category_is_created_for_user(self):
        Category.objects.create(user=self.a_user, name='Education', material_ui_icon_name='School')
        self.assertEqual(len(Category.categories_from_user(self.a_user)), 6)

    def test_category_from_user_is_deleted(self):
        category_created = Category.objects.create(user=self.a_user, name='Car Maintainment', material_ui_icon_name='CarRepair')
        category_created.delete()
        self.assertEqual(len(Category.categories_from_user(self.a_user)), 5)

    def test_created_category_is_not_static(self):
        category_created = Category.objects.create(user=self.a_user, name='Storage', material_ui_icon_name='SdCard')
        self.assertFalse(category_created.static)

    def test_a_default_categories_is_static(self):
        category_created = Category.objects.all()[randint(0, Category.objects.all().count()-1)]
        self.assertTrue(category_created.static)

    def test_two_categories_with_same_name_should_not_be_created_for_a_user(self):
        Category.objects.create(user=self.a_user, name='A Category', material_ui_icon_name='ShuffleRounded')

        with self.assertRaisesMessage(ValidationError, "User cannot create another repeated category"):
            Category.objects.create(user=self.a_user, name='A Category', material_ui_icon_name='Car')

    def test_category_dictionary_serialization(self):
        category_created = Category.objects.create(user=self.a_user, name='Storage', material_ui_icon_name='SdCard')
        self.assertEqual(category_created.as_dict['id'], category_created.id)
        self.assertEqual(category_created.as_dict['name'],  'Storage')
        self.assertEqual(category_created.as_dict['material_ui_icon_name'], 'SdCard')
        self.assertEqual(category_created.as_dict['color'], category_created.color)
        self.assertFalse(category_created.as_dict['static'])
