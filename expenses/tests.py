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
        self.a_user = User.objects.create(
            firebase_uid=create_random_string(FIREBASE_UID_LENGTH))
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
                date='2015-01-01',
                category=self.category_for_expense,
                name="Custom Expense"
            )

    def test_category_dictionary_serialization(self):
        self.assertDictEqual(self.expense_created.as_dict, {
            'id': self.expense_created.id,
            'value': 250.5,
            'category': self.category_for_expense.as_dict,
            'name': "Custom Expense",
            'date': '2022-05-12'
        })


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

        response = self.client.delete(
            self.endpoint, {'id': '1'}, format='json')

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

        expected_response = {
            'id': 1,
            'value': 59999.0,
            'date': '2021-03-25',
            'category': {'id': 2, 'material_ui_icon_name': 'Casino', 'name': 'entretenimiento y ocio', 'static': True},
            'name': 'Expensive Expense'
        }

        self.assertDictEqual(response.json()[0], expected_response)

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

        expected_response = {
            'id': 1,
            'value': 87444.0,
            'date': '2020-02-05',
            'category': {'id': 1, 'material_ui_icon_name': 'AccountBalance', 'name': 'impuestos y servicios', 'static': True},
            'name': "Modified Expense"
        }

        self.assertDictEqual(response.json()[0], expected_response)

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

        expected_response = {
            'id': 1,
            'value': 250.5,
            'date': '2021-01-30',
            'category': {'id': 1, 'material_ui_icon_name': 'AccountBalance', 'name': 'impuestos y servicios', 'static': True},
            'name': "Another expense"
        }

        self.assertDictEqual(response.json()[0], expected_response)

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
