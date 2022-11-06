from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
import os

from categories.models import Category
from users.constants import FIREBASE_UID_LENGTH
from utils import create_random_string
from users.models import User
from budgets.models import Budget
from django.db.utils import IntegrityError

# Create your tests here.
class TestCategoriesModel(TestCase):

    def setUp(self):
        self.a_user = User.objects.create(
            firebase_uid=create_random_string(FIREBASE_UID_LENGTH))
    
    def test_a_budget_is_created_and_has_a_total_limit_with_one_category(self):
        new_budget = Budget.objects.create(user=self.a_user, initial_date='2022-12-5', final_date='2023-12-5')
        new_budget.add_detail(Category.objects.all()[0], 50000.0)
        self.assertEqual(new_budget.total_limit, 50000.0)

    def test_a_budget_is_created_and_has_a_total_limit_with_more_categories(self):
        new_budget = Budget.objects.create(user=self.a_user, initial_date='2022-12-5', final_date='2023-12-5')

        new_budget.add_detail(Category.objects.all()[0], 10000)
        new_budget.add_detail(Category.objects.all()[1], 10000)
        new_budget.add_detail(Category.objects.all()[2], 15000)

        self.assertEqual(new_budget.total_limit, 35000)

    def test_a_budget_cannot_be_created_with_details_of_same_category(self):
        with self.assertRaises(Exception) as raised:  # top level exception as we want to figure out its exact type
            new_budget = Budget.objects.create(user=self.a_user, initial_date='2022-12-5', final_date='2023-12-5')
            new_budget.add_detail(Category.objects.all()[0], 10000)
            new_budget.add_detail(Category.objects.all()[0], 50000)

        self.assertEqual(IntegrityError, type(raised.exception))

    def test_budget_cannot_be_started_in_the_past(self):
        with self.assertRaisesMessage(ValidationError, "{'initial_date': ['Budget date cannot be in the past.']}"):
            Budget.objects.create(user=self.a_user, initial_date='2021-05-5', final_date='2024-02-1')

"""
class TestCategoriesView(APITestCase):
    pass
"""