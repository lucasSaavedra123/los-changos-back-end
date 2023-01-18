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
from datetime import date
from random import choice



# Create your tests here.
class TestExpensesModel(TestCase):
    def setUp(self):
        self.a_user = User.objects.create(
            firebase_uid=create_random_string(FIREBASE_UID_LENGTH))
        self.category_for_expense = Category.objects.all()[0]
        self.another_category = Category.objects.all()[1]
        self.expense_created = Expense.objects.create(
            user=self.a_user,
            value=250.50,
            date='2022-05-12',
            category=self.category_for_expense,
            name="Custom Expense"
        )
    
    def pick_random_category(self):
        return choice(Category.objects.all())

    def test_expense_is_created_for_user(self):
        self.assertEqual(len(Expense.expenses_from_user(self.a_user)), 1)

    def test_expense_from_user_is_deleted(self):
        self.expense_created.delete()
        self.assertEqual(len(Expense.expenses_from_user(self.a_user)), 0)

    def test_future_expenses_cannot_be_created(self):
        with self.assertRaisesMessage(ValidationError, "Expense date cannot be in the future."):
            Expense.objects.create(
                user=self.a_user,
                value=1500.45,
                date='2048-01-01',
                category=self.pick_random_category(),
                name="A Future Expense"
            )

    def test_negative_expenses_cannot_be_created(self):
        with self.assertRaisesMessage(ValidationError, "Ensure this value is greater than or equal to 0.01."):
            Expense.objects.create(
                user=self.a_user,
                value=-58.25,
                date='2015-01-01',
                category=self.pick_random_category(),
                name="Custom Expense"
            )

    def test_expenses_with_too_decimal_digits_values_cannot_be_created(self):
        with self.assertRaisesMessage(ValidationError, "Ensure that there are no more than 2 decimal places."):
            Expense.objects.create(
                user=self.a_user,
                value=145.336667,
                date='2015-01-01',
                category=self.pick_random_category(),
                name="Custom Expense"
            )

    def test_expense_dictionary_serialization(self):
        self.assertDictEqual(self.expense_created.as_dict, {
            'id': self.expense_created.id,
            'value': 250.50,
            'category': self.category_for_expense.as_dict,
            'name': "Custom Expense",
            'date': '2022-05-12'
        })

    def test_expense_from_one_date_is_obtained(self):
        a_date = date(2022, 5, 12)
        filtered_expenses = Expense.filter_within_timeline_from_user(self.a_user, a_date, a_date)

        self.assertEqual(len(filtered_expenses), 1)
        self.assertEqual(filtered_expenses[0], self.expense_created)

    def test_expenses_from_one_date_are_obtained(self):
        self.another_expense_created = Expense.objects.create(
            user=self.a_user,
            value=240,
            date='2022-05-12',
            category=self.category_for_expense,
            name="Another custom expense"
        )

        a_date = date(2022, 5, 12)
        filtered_expenses = Expense.filter_within_timeline_from_user(self.a_user, a_date, a_date)

        self.assertEqual(len(filtered_expenses), 2)
        self.assertEqual(filtered_expenses[0], self.expense_created)
        self.assertEqual(filtered_expenses[1], self.another_expense_created)

    def test_expenses_with_extended_timeline_are_filtered(self):
        another_expense_created = Expense.objects.create(
            user=self.a_user,
            value=240,
            date='2022-05-12',
            category=self.category_for_expense,
            name="Another custom expense"
        )

        Expense.objects.create(
            user=self.a_user,
            value=240,
            date='2022-01-10',
            category=self.category_for_expense,
            name="Old Expense"
        )

        a_date = date(2022, 5, 12)
        filtered_expenses = Expense.filter_within_timeline_from_user(self.a_user, a_date, a_date)

        self.assertEqual(len(filtered_expenses), 2)
        self.assertEqual(filtered_expenses[0], self.expense_created)
        self.assertEqual(filtered_expenses[1], another_expense_created)

    def test_expenses_with_extended_timeline_are_not_filtered(self):
        another_expense_created = Expense.objects.create(
            user=self.a_user,
            value=240,
            date='2022-04-10',
            category=self.category_for_expense,
            name="Another custom expense"
        )

        old_expense = Expense.objects.create(
            user=self.a_user,
            value=240,
            date='2021-01-10',
            category=self.category_for_expense,
            name="Old Expense"
        )

        filtered_expenses = Expense.filter_within_timeline_from_user(self.a_user, date(2021, 1, 1), date(2022, 6, 1))

        self.assertEqual(len(filtered_expenses), 3)
        self.assertEqual(filtered_expenses[0], self.expense_created)
        self.assertEqual(filtered_expenses[1], another_expense_created)
        self.assertEqual(filtered_expenses[2], old_expense)

    def test_expense_with_specific_category_from_one_date_is_obtained(self):
        a_date = date(2022, 5, 12)
        filtered_expenses = Expense.filter_by_category_within_timeline_from_user(self.a_user, a_date, a_date, self.category_for_expense)

        self.assertEqual(len(filtered_expenses), 1)
        self.assertEqual(filtered_expenses[0], self.expense_created)

    def test_expenses_with_specific_category_from_one_date_are_obtained(self):
        self.another_expense_created = Expense.objects.create(
            user=self.a_user,
            value=240,
            date='2022-05-12',
            category=self.category_for_expense,
            name="Another custom expense"
        )

        a_date = date(2022, 5, 12)
        filtered_expenses = Expense.filter_by_category_within_timeline_from_user(self.a_user, a_date, a_date, self.category_for_expense)

        self.assertEqual(len(filtered_expenses), 2)
        self.assertEqual(filtered_expenses[0], self.expense_created)
        self.assertEqual(filtered_expenses[1], self.another_expense_created)

    def test_expenses_with_same_category_with_extended_timeline_are_filtered(self):
        another_expense_created = Expense.objects.create(
            user=self.a_user,
            value=240,
            date='2022-05-12',
            category=self.category_for_expense,
            name="Another custom expense"
        )

        Expense.objects.create(
            user=self.a_user,
            value=240,
            date='2022-01-10',
            category=self.another_category,
            name="Old Expense"
        )

        filtered_expenses = Expense.filter_by_category_within_timeline_from_user(self.a_user, date(2021, 1, 2), date(2022, 6, 1), self.category_for_expense)

        self.assertEqual(len(filtered_expenses), 2)
        self.assertEqual(filtered_expenses[0], self.expense_created)
        self.assertEqual(filtered_expenses[1], another_expense_created)

    def test_expenses_with_specific_category_with_extended_timeline_are_filtered(self):
        another_expense_created = Expense.objects.create(
            user=self.a_user,
            value=240,
            date='2022-04-10',
            category=self.category_for_expense,
            name="Another custom expense"
        )

        old_expense = Expense.objects.create(
            user=self.a_user,
            value=240,
            date='2021-01-10',
            category=self.category_for_expense,
            name="Old Expense"
        )

        filtered_expenses = Expense.filter_by_category_within_timeline_from_user(self.a_user, date(2021, 1, 1), date(2022, 6, 1), self.category_for_expense)

        self.assertEqual(len(filtered_expenses), 3)
        self.assertEqual(filtered_expenses[0], self.expense_created)
        self.assertEqual(filtered_expenses[1], another_expense_created)
        self.assertEqual(filtered_expenses[2], old_expense)
