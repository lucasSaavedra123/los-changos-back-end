import os

from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from categories.models import Category
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from users.models import User
from utils import create_random_string
from users.constants import FIREBASE_UID_LENGTH
from .models import Expense


# Create your tests here.
class TestExpensesModel(TestCase):
    def setUp(self):
        self.a_user = User.objects.create(firebase_uid=create_random_string(FIREBASE_UID_LENGTH))
        self.category_for_expense = Category.objects.all()[0]
        self.expense_created = Expense.objects.create(
            user=self.a_user,
            value=250.5,
            date='2022-05-12',
            category=self.category_for_expense,
            name="Custom Expense"
        )

    def test_expense_is_created_for_user(self):
        self.assertEqual(len(Expense.expenses_from_user(self.a_user)), 1)

    def test_expense_from_user_is_deleted(self):
        self.expense_created.delete()
        self.assertEqual(len(Expense.expenses_from_user(self.a_user)), 0)

    def test_future_expenses_cannot_be_created(self):
        with self.assertRaises(ValidationError):
            Expense.objects.create(
                user=self.a_user,
                value=1500,
                date='2988-01-01',
                category=self.category_for_expense,
                name="Custom Expense"
            )

    def test_negative_expenses_cannot_be_created(self):
        with self.assertRaises(ValidationError):
            Expense.objects.create(
                user=self.a_user,
                value=-58.25,
                date='2988-01-01',
                category=self.category_for_expense,
                name="Custom Expense"
            )

    def test_category_dictionary_serialization(self):
        self.assertDictEqual(self.expense_created.as_dict,{
                'id': self.expense_created.id,
                'value':250.5,
                'category': self.category_for_expense.as_dict,
                'name':"Custom Expense",
                'date':'2022-05-12'
            })

class TestExpensesView(APITestCase):
    def setUp(self):
        pass
