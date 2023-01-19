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
import datetime

# Create your tests here.
class TestExpensesModel(TestCase):
    def setUp(self):
        self.a_user = User.objects.create(
            firebase_uid=create_random_string(FIREBASE_UID_LENGTH))
        self.category_for_expense = Category.objects.all()[0]
        self.another_category = Category.objects.all()[1]

    def pick_random_category(self):
        return choice(Category.objects.all())

    def test_user_has_no_expenses(self):
        self.assertEqual(len(Expense.expenses_from_user(self.a_user)), 0) 

    def test_expense_is_created_for_user(self):
        Expense.objects.create(
            user=self.a_user,
            value=1500.50,
            date='2021-04-05',
            category=self.category_for_expense,
            name="Custom Expense"
        )

        self.assertEqual(len(Expense.expenses_from_user(self.a_user)), 1)

    def test_expense_from_user_is_deleted(self):
        expense_created = Expense.objects.create(
            user=self.a_user,
            value=1500.50,
            date='2021-04-05',
            category=self.category_for_expense,
            name="To Delete"
        )

        expense_created.delete()
        self.assertEqual(len(Expense.expenses_from_user(self.a_user)), 0)

    def test_future_expenses_cannot_be_created_in_the_next_year(self):
        with self.assertRaisesMessage(ValidationError, "Expense date cannot be in the future."):
            Expense.objects.create(
                user=self.a_user,
                value=1500.45,
                date=f'{datetime.date.today().year+1}-07-20',
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
                name="A negative Expense"
            )

    def test_expenses_with_too_decimal_digits_values_cannot_be_created(self):
        with self.assertRaisesMessage(ValidationError, "Ensure that there are no more than 2 decimal places."):
            Expense.objects.create(
                user=self.a_user,
                value=145.336667,
                date='2015-01-01',
                category=self.pick_random_category(),
                name="Too exact expense"
            )

    def test_expenses_with_invalid_date_cannot_be_created(self):
        with self.assertRaises(ValidationError):
            e = Expense.objects.create(
                user=self.a_user,
                value=100,
                date='1222-98-122',
                category=self.pick_random_category(),
                name="Imaginary Expense"
            )

    def test_expense_dictionary_serialization(self):
        
        category_for_expense = self.pick_random_category()

        expense = Expense.objects.create(
            user=self.a_user,
            value=100.00,
            date='2015-05-30',
            category=category_for_expense,
            name="A Cheap Expense"
        )

        self.assertDictEqual(expense.as_dict, {
            'id': expense.id,
            'date': "2015-05-30",
            'category': category_for_expense.as_dict,
            'value': 100.00,
            'name': "A Cheap Expense",
            'future_expense': False
        })

    def test_expense_from_one_date_is_obtained(self):
        expense_created = Expense.objects.create(
            user=self.a_user,
            value=250044,
            date='2020-05-06',
            category=self.category_for_expense,
            name="Custom Expense"
        )

        a_date = date(2020, 5, 6)
        filtered_expenses = Expense.filter_within_timeline_from_user(self.a_user, a_date, a_date)

        self.assertEqual(len(filtered_expenses), 1)
        self.assertEqual(filtered_expenses[0], expense_created)

    def test_expenses_from_one_date_are_obtained(self):
        expense_created_one = Expense.objects.create(
            user=self.a_user,
            value=1500,
            date='2021-09-10',
            category=self.category_for_expense,
            name="Custom expense"
        )

        expense_created_two = Expense.objects.create(
            user=self.a_user,
            value=1500,
            date='2021-09-10',
            category=self.category_for_expense,
            name="Custom Expense"
        )

        Expense.objects.create(
            user=self.a_user,
            value=1500,
            date='2020-02-02',
            category=self.category_for_expense,
            name="Custom Expense"
        )

        a_date = date(2021, 9, 10)
        filtered_expenses = Expense.filter_within_timeline_from_user(self.a_user, a_date, a_date)

        self.assertEqual(len(filtered_expenses), 2)
        self.assertEqual(filtered_expenses[0], expense_created_one)
        self.assertEqual(filtered_expenses[1], expense_created_two)

    def test_expenses_with_extended_timeline(self):
        expense_one = Expense.objects.create(
            user=self.a_user,
            value=100,
            date='2021-06-1',
            category=self.category_for_expense,
            name="Old expense Two"
        )

        expense_two = Expense.objects.create(
            user=self.a_user,
            value=558,
            date='2021-01-10',
            category=self.category_for_expense,
            name="Old expense One"
        )

        Expense.objects.create(
            user=self.a_user,
            value=3666.5,
            date='2022-5-10',
            category=self.category_for_expense,
            name="Old expense Three"
        )

        filtered_expenses = Expense.filter_within_timeline_from_user(self.a_user, date(2021, 1, 1), date(2022, 1, 1))

        self.assertEqual(len(filtered_expenses), 2)
        self.assertTrue(expense_one in filtered_expenses)
        self.assertTrue(expense_two in filtered_expenses)

    def test_expense_with_specific_category_from_one_date_is_obtained(self):
        category_for_expense = self.pick_random_category()

        expense = Expense.objects.create(
            user=self.a_user,
            value=500.00,
            date='2022-05-12',
            category=category_for_expense,
            name="A Cheap Expense"
        )

        a_date = date(2022, 5, 12)
        filtered_expenses = Expense.filter_by_category_within_timeline_from_user(self.a_user, a_date, a_date, category_for_expense)

        self.assertEqual(len(filtered_expenses), 1)
        self.assertEqual(filtered_expenses[0], expense)

    def test_expenses_with_specific_category_from_one_date_are_obtained(self):  
        category_for_expense = self.pick_random_category()

        expense_one = Expense.objects.create(
            user=self.a_user,
            value=500.00,
            date='2018-01-01',
            category=category_for_expense,
            name="500 Expense"
        )

        expense_two = Expense.objects.create(
            user=self.a_user,
            value=240,
            date='2018-01-01',
            category=category_for_expense,
            name="240 Expense"
        )

        a_date = date(2018, 1, 1)
        filtered_expenses = Expense.filter_by_category_within_timeline_from_user(self.a_user, a_date, a_date, category_for_expense)

        self.assertEqual(len(filtered_expenses), 2)
        self.assertTrue(expense_two in filtered_expenses)
        self.assertTrue(expense_one in filtered_expenses)

    def test_expenses_with_same_category_with_extended_timeline_are_filtered(self):
        category_for_expense = self.pick_random_category()

        expense_one = Expense.objects.create(
            user=self.a_user,
            value=500.00,
            date='2018-01-01',
            category=category_for_expense,
            name="500 Expense"
        )

        expense_two = Expense.objects.create(
            user=self.a_user,
            value=240,
            date='2020-05-01',
            category=category_for_expense,
            name="240 Expense"
        )

        filtered_expenses = Expense.filter_by_category_within_timeline_from_user(self.a_user, date(2018, 1, 1), date(2021, 1, 1), category_for_expense)

        self.assertEqual(len(filtered_expenses), 2)
        self.assertTrue(expense_two in filtered_expenses)
        self.assertTrue(expense_one in filtered_expenses)

    def test_expenses_with_specific_category_with_extended_timeline_are_filtered(self):
        expense_one = Expense.objects.create(
            user=self.a_user,
            value=500.00,
            date='2018-01-01',
            category=Category.objects.all()[0],
            name="500 Expense"
        )

        Expense.objects.create(
            user=self.a_user,
            value=240,
            date='2020-05-01',
            category=Category.objects.all()[1],
            name="240 Expense"
        )

        filtered_expenses = Expense.filter_by_category_within_timeline_from_user(self.a_user, date(2018, 1, 1), date(2021, 1, 1), Category.objects.all()[0])

        self.assertEqual(len(filtered_expenses), 1)
        self.assertTrue(expense_one in filtered_expenses)
