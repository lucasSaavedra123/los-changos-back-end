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
from expenses.models import Expense

# Create your tests here.
class TestBudgetsModel(TestCase):

    def setUp(self):
        self.a_user = User.objects.create(
            firebase_uid=create_random_string(FIREBASE_UID_LENGTH))

    def test_a_budget_is_created_and_has_a_total_limit_with_one_category(self):
        new_budget = Budget.objects.create(user=self.a_user, initial_date='2022-12-5', final_date='2023-12-5')
        new_budget.add_limit(Category.objects.all()[0], 50000.0)
        self.assertEqual(new_budget.total_limit, 50000.0)

    def test_a_budget_is_created_and_has_a_total_limit_with_more_categories(self):
        new_budget = Budget.objects.create(user=self.a_user, initial_date='2022-12-5', final_date='2023-12-5')

        new_budget.add_limit(Category.objects.all()[0], 10000)
        new_budget.add_limit(Category.objects.all()[1], 10000)
        new_budget.add_limit(Category.objects.all()[2], 15000)

        self.assertEqual(new_budget.total_limit, 35000)

    def test_a_budget_cannot_be_created_with_details_of_same_category(self):
        with self.assertRaises(Exception) as raised:
            new_budget = Budget.objects.create(user=self.a_user, initial_date='2022-12-5', final_date='2023-12-5')
            new_budget.add_limit(Category.objects.all()[0], 10000)
            new_budget.add_limit(Category.objects.all()[0], 50000)

        self.assertEqual(IntegrityError, type(raised.exception))

    def test_budget_cannot_be_finished_in_the_past(self):
        with self.assertRaisesMessage(ValidationError, "Budget date cannot be in the past."):
            Budget.objects.create(user=self.a_user, initial_date='2020-05-5', final_date='2021-01-1')

    def test_budget_initial_date_should_be_earlier_than_final_date(self):
        with self.assertRaisesMessage(ValidationError, "Budget initial date should be earlier than final date."):
            Budget.objects.create(user=self.a_user, initial_date='2050-05-5', final_date='2030-01-5')

    def test_user_can_create_two_budgets_that_not_overlap(self):
        Budget.objects.create(user=self.a_user, initial_date='2022-12-5', final_date='2023-12-5')
        Budget.objects.create(user=self.a_user, initial_date='2023-12-6', final_date='2027-05-1')
        self.assertEqual(len(Budget.all_from_user(self.a_user)), 2)

    def test_user_cannot_create_two_budgets_that_overlap_partially(self):
        Budget.objects.create(user=self.a_user, initial_date='2026-01-01', final_date='2028-01-01')

        with self.assertRaisesMessage(ValidationError, "Budget is overlapping with another one."):
            Budget.objects.create(
                user=self.a_user, initial_date='2025-01-01', final_date='2027-01-01')

        with self.assertRaisesMessage(ValidationError, "Budget is overlapping with another one."):
            Budget.objects.create(
                user=self.a_user, initial_date='2027-01-01', final_date='2030-01-01')

    def test_user_cannot_create_two_budgets_that_overlap_completely(self):
        Budget.objects.create(
            user=self.a_user, initial_date='2022-12-5', final_date='2023-12-5')

        with self.assertRaisesMessage(ValidationError, "Budget is overlapping with another one."):
            Budget.objects.create(
                user=self.a_user, initial_date='2022-12-5', final_date='2023-12-1')

    def test_user_add_expense_in_budget(self):
        new_budget = Budget.objects.create(
            user=self.a_user, initial_date='2020-01-01', final_date='2025-01-01')

        details = [
            new_budget.add_limit(Category.objects.all()[0], 10000),
            new_budget.add_limit(Category.objects.all()[1], 10000),
            new_budget.add_limit(Category.objects.all()[2], 15000)
        ]

        Expense.create_expense_for_user(
            self.a_user, date='2021-01-30', value=5000, category=Category.objects.all()[0], name='New Expense')

        self.assertEqual(details[0].total_spent, 5000)
        self.assertEqual(details[1].total_spent, 0)
        self.assertEqual(details[2].total_spent, 0)
        self.assertEqual(new_budget.total_spent, 5000)

    def test_user_add_several_expenses_in_budget(self):
        new_budget = Budget.objects.create(
            user=self.a_user, initial_date='2020-01-01', final_date='2025-01-01')

        details = [
            new_budget.add_limit(Category.objects.all()[0], 10000),
            new_budget.add_limit(Category.objects.all()[1], 10000),
            new_budget.add_limit(Category.objects.all()[2], 15000)
        ]

        Expense.create_expense_for_user(
            self.a_user, date='2021-02-05', value=5000, category=Category.objects.all()[0], name='New Expense')
        Expense.create_expense_for_user(
            self.a_user, date='2022-01-30', value=2500, category=Category.objects.all()[1], name='New Expense')
        Expense.create_expense_for_user(
            self.a_user, date='2020-05-30', value=5000, category=Category.objects.all()[1], name='New Expense')
        Expense.create_expense_for_user(
            self.a_user, date='2020-11-12', value=1000, category=Category.objects.all()[3], name='New Expense')

        self.assertEqual(details[0].total_spent, 5000)
        self.assertEqual(details[1].total_spent, 7500)
        self.assertEqual(details[2].total_spent, 0)
        self.assertEqual(new_budget.total_spent, 12500)

    def test_user_add_to_budget_future_expense_along_limits_details(self):
        new_budget = Budget.objects.create(
            user=self.a_user, initial_date='2020-01-01', final_date='2025-01-01')

        details = [
            new_budget.add_limit(Category.objects.all()[0], 10000),
            new_budget.add_limit(Category.objects.all()[1], 10000),
            new_budget.add_future_expense(
                Category.objects.all()[4], 4500, 'AySa Bill', '2023-01-01')
        ]

        self.assertEqual(details[2].value, 4500)
        self.assertEqual(details[2].expiration_date.strftime("%Y-%m-%d"), '2023-01-01')
        self.assertEqual(details[2].name, 'AySa Bill')

    def test_user_add_a_future_expense_detail(self):
        new_budget = Budget.objects.create(
            user=self.a_user, initial_date='2024-01-01', final_date='2025-01-01')

        details = [
            new_budget.add_limit(Category.objects.all()[0], 10000),
            new_budget.add_limit(Category.objects.all()[1], 10000),
            new_budget.add_future_expense(
                Category.objects.all()[4], 4500, 'AySa Bill', '2024-05-07')
        ]

        self.assertEqual(details[2].value, 4500)
        self.assertEqual(details[2].expiration_date.strftime("%Y-%m-%d"), '2024-05-07')
        self.assertEqual(details[2].name, 'AySa Bill')
        self.assertEqual(details[2].expended, False)

    def test_user_cannot_create_future_expense_out_of_budget_dates(self):
        new_budget = Budget.objects.create(
            user=self.a_user, initial_date='2024-01-01', final_date='2025-01-01')

        with self.assertRaisesMessage(ValidationError, "Future Expense has to be between the budget dates."):
            new_budget.add_future_expense(Category.objects.all()[4], 4500, 'AySa Bill', '2020-05-07')

        with self.assertRaisesMessage(ValidationError, "Future Expense has to be between the budget dates."):
            new_budget.add_future_expense(Category.objects.all()[4], 4500, 'AySa Bill', '2028-01-01')
