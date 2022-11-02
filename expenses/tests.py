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


# Create your tests here.
class TestExpensesModel(TestCase):
    def assertActionInSecureEnvironment(self, action):
        os.environ["ENVIRONMENT"] = "PROD"
        self.assertEqual(action(self).status_code, status.HTTP_401_UNAUTHORIZED)
        os.environ["ENVIRONMENT"] = "DEV"

    def setUp(self):
        self.a_user = User.objects.create(
            firebase_uid=create_random_string(FIREBASE_UID_LENGTH))
        self.category_for_expense = Category.objects.all()[0]
        self.another_category = Category.objects.all()[1]
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
        with self.assertRaisesMessage(ValidationError, "{'date': ['Expense date cannot be in the future.']}"):
            Expense.objects.create(
                user=self.a_user,
                value=1500,
                date='2988-01-01',
                category=self.category_for_expense,
                name="Custom Expense"
            )

    def test_negative_expenses_cannot_be_created(self):
        with self.assertRaisesMessage(ValidationError, "{'value': ['Ensure this value is greater than or equal to 0.01.']}"):
            Expense.objects.create(
                user=self.a_user,
                value=-58.25,
                date='2015-01-01',
                category=self.category_for_expense,
                name="Custom Expense"
            )

    def test_expense_dictionary_serialization(self):
        self.assertDictEqual(self.expense_created.as_dict, {
            'id': self.expense_created.id,
            'value': 250.5,
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


class TestExponsesView(APITestCase):
    def setUp(self):
        self.endpoint = '/expense'

    def test_user_creates_expenses(self):
        response = self.client.post(self.endpoint, {
            'value': 250.5,
            'date': '2022-05-12',
            'category_id': 2,
            'name': "Last Expense of the month"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_delete_created_expense(self):
        response = self.client.post(self.endpoint, {
            'value': 250.5,
            'date': '2021-01-30',
            'category_id': 3,
            'name': "Another expense"
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.delete(self.endpoint, {'id': '1'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.json(), [])

    def test_user_cannot_delete_another_user_expense(self):
        another_user = User.objects.create(
            firebase_uid=create_random_string(FIREBASE_UID_LENGTH))

        Expense.create_expense_for_user(another_user, name='Random expense',
                                        date='2019-01-30', value=100, category=Category.objects.all()[1])

        response = self.client.delete(
            self.endpoint, {'id': '1'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_modify_another_user_expense(self):
        another_user = User.objects.create(
            firebase_uid=create_random_string(FIREBASE_UID_LENGTH))

        Expense.create_expense_for_user(another_user, name='Random expense',
                                        date='2019-01-30', value=100, category=Category.objects.all()[1])

        response = self.client.patch(self.endpoint, {
            'id': 1,
            'value': 100,
            'date': '2021-01-30',
            'category_id': 1,
            'name': "Another expense"
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_reads_expenses(self):
        response = self.client.post(self.endpoint, {
            'value': 59999,
            'date': '2021-03-25',
            'category_id': 2,
            'name': "Expensive Expense"
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()[0]

        self.assertEqual(json_response['value'], 59999.0)
        self.assertEqual(json_response['date'], '2021-03-25')
        self.assertEqual(json_response['category']['id'], 2)
        self.assertEqual(json_response['name'], 'Expensive Expense')

    def test_user_update_all_information_related_to_category_expense(self):
        self.client.post(self.endpoint, {
            'value': 250.5,
            'date': '2021-01-30',
            'category_id': 3,
            'name': "Another expense"
        }, format='json')

        self.client.patch(self.endpoint, {
            'id': 1,
            'value': 87444,
            'date': '2020-02-05',
            'category_id': 1,
            'name': "Modified Expense"
        }, format='json')

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()[0]

        self.assertEqual(json_response['value'], 87444.0)
        self.assertEqual(json_response['date'], '2020-02-05')
        self.assertEqual(json_response['category']['id'], 1)
        self.assertEqual(json_response['name'], "Modified Expense")

    def test_user_update_only_category_of_created_expense(self):
        self.client.post(self.endpoint, {
            'value': 250.5,
            'date': '2021-01-30',
            'category_id': 3,
            'name': "Another expense"
        }, format='json')

        self.client.patch(self.endpoint, {
            'id': 1,
            'value': 250.5,
            'date': '2021-01-30',
            'category_id': 1,
            'name': "Another expense"
        }, format='json')

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()[0]

        self.assertEqual(json_response['value'], 250.5)
        self.assertEqual(json_response['date'], '2021-01-30')
        self.assertEqual(json_response['category']['id'], 1)
        self.assertEqual(json_response['name'], "Another expense")

    def test_user_forgots_to_include_field_in_create_request(self):
        response = self.client.post(self.endpoint, {
            'date': '2021-01-30',
            'category_id': 3,
            'name': "Another expense"
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_forgots_to_include_field_in_patch_request(self):
        response = self.client.patch(self.endpoint, {
            'value': 250.5,
            'date': '2021-01-30'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_reads_expense_from_a_specific_time_line(self):
        self.client.post(self.endpoint, {
            'value': 10599,
            'date': '2021-06-20',
            'category_id': 1,
            'name': "Another expense"
        }, format='json')

        self.client.post(self.endpoint, {
            'value': 123456,
            'date': '2022-06-02',
            'category_id': 3,
            'name': "Another expense"
        }, format='json')

        response = self.client.post(self.endpoint + "/filter", {
            "timeline": ["2022-06-02", "2022-06-02"]
        }, format='json')

        self.assertEqual(response.json()[0]['category']['id'], 3)

    def test_user_reads_expenses_within_extended_time_line(self):
        self.client.post(self.endpoint, {
            'value': 10599,
            'date': '2021-05-20',
            'category_id': 1,
            'name': "Very old expense"
        }, format='json')

        self.client.post(self.endpoint, {
            'value': 123456,
            'date': '2022-06-02',
            'category_id': 3,
            'name': "Another expense"
        }, format='json')

        response = self.client.post(self.endpoint + "/filter", {
            "timeline": ["2021-01-01", "2023-01-01"]
        }, format='json')

        json_response_one = response.json()[0]
        json_response_two = response.json()[1]

        self.assertEqual(json_response_one['value'], 123456.0)
        self.assertEqual(json_response_one['date'], '2022-06-02')
        self.assertEqual(json_response_one['category']['id'], 3)
        self.assertEqual(json_response_one['name'], "Another expense")

        self.assertEqual(json_response_two['value'], 10599.0)
        self.assertEqual(json_response_two['date'], '2021-05-20')
        self.assertEqual(json_response_two['category']['id'], 1)
        self.assertEqual(json_response_two['name'], 'Very old expense')

    def test_user_reads_expenses_within_extended_time_line_of_a_specific_category(self):
        self.client.post(self.endpoint, {
            'value': 10599,
            'date': '2021-05-20',
            'category_id': 1,
            'name': "Very old expense"
        }, format='json')

        self.client.post(self.endpoint, {
            'value': 10500,
            'date': '2021-12-30',
            'category_id': 1,
            'name': "Same category very old expense"
        }, format='json')

        self.client.post(self.endpoint, {
            'value': 123456,
            'date': '2022-06-02',
            'category_id': 3,
            'name': "Another expense"
        }, format='json')

        response = self.client.post(self.endpoint + "/filter", {
            "timeline": ["2021-01-01", "2023-01-01"],
            "category_id": 1
        }, format='json')

        self.assertEqual(len(response.json()), 2)

        json_response_one = response.json()[0]
        json_response_two = response.json()[1]

        self.assertEqual(json_response_one['value'], 10500.0)
        self.assertEqual(json_response_one['date'], '2021-12-30')
        self.assertEqual(json_response_one['category']['id'], 1)
        self.assertEqual(json_response_one['name'], 'Same category very old expense')

        self.assertEqual(json_response_two['value'], 10599.0)
        self.assertEqual(json_response_two['date'], '2021-05-20')
        self.assertEqual(json_response_two['category']['id'], 1)
        self.assertEqual(json_response_two['name'], "Very old expense")

    def test_user_has_no_provide_valid_token_to_read_expenses(self):
        os.environ["ENVIRONMENT"] = "PROD"
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        os.environ["ENVIRONMENT"] = "DEV"

    def test_user_has_no_provide_valid_token_to_add_expense(self):
        os.environ["ENVIRONMENT"] = "PROD"
        response = self.client.post(self.endpoint, {
            'value': 250.5,
            'date': '2021-01-30',
            'category_id': 3,
            'name': "Another expense"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        os.environ["ENVIRONMENT"] = "DEV"

    def test_user_has_no_provide_valid_token_to_patch_expense(self):
        os.environ["ENVIRONMENT"] = "PROD"
        response = self.client.patch(self.endpoint, {
            'id': 1444,
            'value': 250.5,
            'date': '2021-01-30',
            'category_id': 3,
            'name': "Another expense"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        os.environ["ENVIRONMENT"] = "DEV"

    def test_user_has_no_provide_valid_token_to_delete_expensey(self):
        os.environ["ENVIRONMENT"] = "PROD"
        response = self.client.delete(
            self.endpoint, {'id': 777}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        os.environ["ENVIRONMENT"] = "DEV"
