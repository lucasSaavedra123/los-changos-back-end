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
from .models import SharedExpense
from expenses.models import Expense
from datetime import date

# Create your tests here.
class TestSharedExpensesModel(TestCase):
    def setUp(self):
        self.a_user = User.objects.create(
            firebase_uid=create_random_string(FIREBASE_UID_LENGTH), alias= 'testUser')
        self.anotherUser = User.objects.create( firebase_uid=create_random_string(FIREBASE_UID_LENGTH),alias='anotherUser')
        self.category_for_expense = Category.objects.all()[5]
        self.another_category = Category.objects.all()[1]
        self.shared_expense_created = SharedExpense.objects.create(
            user=self.a_user,
            value=2500,
            date='2022-06-12',
            category=self.category_for_expense,
            name="Custom Expense",
            userToShare= self.anotherUser
        )
        self.another_shared_expense_created = SharedExpense.objects.create(
            user=self.anotherUser,
            value=2500,
            date='2022-06-12',
            category=self.category_for_expense,
            name="Custom Expense",
            userToShare= self.a_user
        )
    def test_shared_expense_is_created_for_user(self):
        self.assertEqual(len(SharedExpense.expenses_from_user(self.a_user)), 1)

    def test_shared_expense_from_user_is_deleted(self):
        self.shared_expense_created.delete()
        self.assertEqual(len(SharedExpense.expenses_from_user(self.a_user)), 0)

    def test_future_expenses_cannot_be_created(self):
        with self.assertRaisesMessage(ValidationError, "{'date': ['Expense date cannot be in the future.']}"):
            SharedExpense.objects.create(
                user=self.a_user,
                value=1500,
                date='2988-01-01',
                category=self.category_for_expense,
                name="Custom Expense",
                userToShare= self.anotherUser
            )

    def test_negative_expenses_cannot_be_created(self):
        with self.assertRaisesMessage(ValidationError, "{'value': ['Ensure this value is greater than or equal to 0.01.']}"):
            SharedExpense.objects.create(
                user=self.a_user,
                value=-58.25,
                date='2015-01-01',
                category=self.category_for_expense,
                name="Custom Expense",
                userToShare= self.anotherUser
            )

    def test_expense_dictionary_serialization(self):
        self.assertDictEqual(self.shared_expense_created.as_dict, {
            'id': self.shared_expense_created.id,
            'user': self.shared_expense_created.user.as_dict,
            'value': 2500,
            'category': self.category_for_expense.as_dict,
            'name': "Custom Expense",
            'date': '2022-06-12',
            'userToShare': self.anotherUser.as_dict,
            'userToShareFlag': self.shared_expense_created.userToShareFlag,
            'aceptedTransaction': self.shared_expense_created.aceptedTransaction,

        })
    def test_expense_from_one_date_is_obtained(self):
        a_date = date(2022, 6, 12)
        filtered_expenses = SharedExpense.filter_within_timeline_from_user(self.a_user, a_date, a_date)

        self.assertEqual(len(filtered_expenses), 1)
        self.assertEqual(filtered_expenses[0], self.shared_expense_created)

    def test_expense_from_one_date_that_is_created_by_other_user_is_obtained(self):
        a_date = date(2022, 6, 12)
        filtered_expenses = SharedExpense.filter_within_timeline_from_otherUser(self.a_user, a_date, a_date)

        self.assertEqual(len(filtered_expenses), 1)
        self.assertEqual(filtered_expenses[0], self.another_shared_expense_created)

    def test_expenses_from_one_date_are_obtained(self):
        self.another_shared_expense_created = SharedExpense.objects.create(
            user=self.a_user,
            value=2500,
            date='2022-06-12',
            category=self.category_for_expense,
            name="Custom Expense",
            userToShare= self.anotherUser
        )


        a_date = date(2022, 6, 12)
        filtered_expenses = SharedExpense.filter_within_timeline_from_user(self.a_user, a_date, a_date)

        self.assertEqual(len(filtered_expenses), 2)
        self.assertEqual(filtered_expenses[0], self.shared_expense_created)
        self.assertEqual(filtered_expenses[1], self.another_shared_expense_created)

    def test_expenses_with_extended_timeline_are_filtered(self):
        another_expense_created = SharedExpense.objects.create(
            user=self.a_user,
            value=240,
            date='2022-06-12',
            category=self.category_for_expense,
            name="Another custom expense",
            userToShare= self.anotherUser

        )

        SharedExpense.objects.create(
            user=self.a_user,
            value=240,
            date='2022-01-10',
            category=self.category_for_expense,
            name="Old Expense",
            userToShare= self.anotherUser
        )

        a_date = date(2022, 6, 12)
        filtered_expenses = SharedExpense.filter_within_timeline_from_user(self.a_user, a_date, a_date)

        self.assertEqual(len(filtered_expenses), 2)
        self.assertEqual(filtered_expenses[0], self.shared_expense_created)
        self.assertEqual(filtered_expenses[1], another_expense_created)
    
    def test_expenses_with_extended_timeline_are_not_filtered(self):
        another_expense_created = SharedExpense.objects.create(
            user=self.a_user,
            value=240,
            date='2022-04-10',
            category=self.category_for_expense,
            name="Another custom expense",
            userToShare= self.anotherUser
        )

        old_expense = SharedExpense.objects.create(
            user=self.a_user,
            value=240,
            date='2021-01-10',
            category=self.category_for_expense,
            name="Old Expense",
            userToShare= self.anotherUser
        )

        filtered_expenses = SharedExpense.filter_within_timeline_from_user(self.a_user, date(2021, 1, 1), date(2022, 6, 12))

        self.assertEqual(len(filtered_expenses), 3)
        self.assertEqual(filtered_expenses[0], self.shared_expense_created)
        self.assertEqual(filtered_expenses[1], another_expense_created)
        self.assertEqual(filtered_expenses[2], old_expense)
    
    def test_expense_with_specific_category_from_one_date_is_obtained(self):
        a_date = date(2022, 6, 12)
        filtered_expenses = SharedExpense.filter_by_category_within_timeline_from_user(self.a_user, a_date, a_date, self.category_for_expense)

        self.assertEqual(len(filtered_expenses), 1)
        self.assertEqual(filtered_expenses[0], self.shared_expense_created)

    def test_expenses_with_specific_category_from_one_date_are_obtained(self):
        self.another_expense_created = SharedExpense.objects.create(
            user=self.a_user,
            value=240,
            date='2022-06-12',
            category=self.category_for_expense,
            name="Another custom expense",
            userToShare= self.anotherUser
        )

        a_date = date(2022, 6, 12)
        filtered_expenses = SharedExpense.filter_by_category_within_timeline_from_user(self.a_user, a_date, a_date, self.category_for_expense)

        self.assertEqual(len(filtered_expenses), 2)
        self.assertEqual(filtered_expenses[0], self.shared_expense_created)
        self.assertEqual(filtered_expenses[1], self.another_expense_created)
    
    def test_expenses_with_same_category_with_extended_timeline_are_filtered(self):
        another_expense_created = SharedExpense.objects.create(
            user=self.a_user,
            value=240,
            date='2022-05-12',
            category=self.category_for_expense,
            name="Another custom expense",
            userToShare= self.anotherUser
        )

        SharedExpense.objects.create(
            user=self.a_user,
            value=240,
            date='2022-01-10',
            category=self.another_category,
            name="Old Expense",
            userToShare= self.anotherUser

        )

        filtered_expenses = SharedExpense.filter_by_category_within_timeline_from_user(self.a_user, date(2021, 1, 2), date(2022, 6, 12), self.category_for_expense)

        self.assertEqual(len(filtered_expenses), 2)
        self.assertEqual(filtered_expenses[0], self.shared_expense_created)
        self.assertEqual(filtered_expenses[1], another_expense_created)

    def test_expenses_with_specific_category_with_extended_timeline_are_filtered(self):
        another_expense_created = SharedExpense.objects.create(
            user=self.a_user,
            value=240,
            date='2022-04-10',
            category=self.category_for_expense,
            name="Another custom expense",
            userToShare= self.anotherUser
        )

        old_expense = SharedExpense.objects.create(
            user=self.a_user,
            value=240,
            date='2021-01-10',
            category=self.category_for_expense,
            name="Old Expense",
            userToShare= self.anotherUser
        )

        filtered_expenses = SharedExpense.filter_by_category_within_timeline_from_user(self.a_user, date(2021, 1, 1), date(2022, 6, 12), self.category_for_expense)

        self.assertEqual(len(filtered_expenses), 3)
        self.assertEqual(filtered_expenses[0], self.shared_expense_created)
        self.assertEqual(filtered_expenses[1], another_expense_created)
        self.assertEqual(filtered_expenses[2], old_expense)

