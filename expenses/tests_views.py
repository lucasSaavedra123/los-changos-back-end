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
class TestExpensesView(APITestCase):
    def assertActionInSecureEnvironment(self, action):
        os.environ["ENVIRONMENT"] = "PROD"
        return_element = action(self)
        os.environ["ENVIRONMENT"] = "DEV"
        return return_element

    def create_expense_with_response(self, value, date, category_id, name, expected_status_code):
        response = self.client.post(self.endpoint, {
            'value': value,
            'date': date,
            'category_id': category_id,
            'name': name
        }, format='json')

        self.assertEqual(response.status_code, expected_status_code)

        return response

    def get_expense_with_response(self, expected_status_code):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, expected_status_code)

        return response

    def delete_expense_with_response(self, id, expected_status_code):
        response = self.client.delete(
            self.endpoint, {'id': str(id)}, format='json')

        self.assertEqual(response.status_code, expected_status_code)

        return response

    def filter_expenses_with_response(self, timeline, category_id, expected_status_code):
        response = self.client.post(self.endpoint + "/filter", {
            "timeline": timeline,
            "category_id": category_id
        }, format='json')

        self.assertEqual(response.status_code, expected_status_code)

        return response

    def patch_expense_with_response(self, id, value, date, category_id, name, expected_status_code):
        response = self.client.patch(self.endpoint, {
            'id': id,
            'value': value,
            'date': date,
            'category_id': category_id,
            'name': name
        }, format='json')

        self.assertEqual(response.status_code, expected_status_code)

        return response

    def assertExpenseInformationIsRight(self, json_response, value, date, category_id, name, future_expense):
        self.assertEqual(json_response['value'], value)
        self.assertEqual(json_response['date'], date)
        self.assertEqual(json_response['category']['id'], category_id)
        self.assertEqual(json_response['name'], name)
        self.assertEqual(json_response['future_expense'], False)

    def setUp(self):
        self.endpoint = '/expense'

    def test_user_creates_expenses(self):
        self.create_expense_with_response(
            250.5, '2022-05-12', 2, "Last Expense of the month", status.HTTP_201_CREATED)
        response = self.get_expense_with_response(status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_user_create_with_value_as_none_expenses(self):
        self.create_expense_with_response(None, '2022-05-12', 2, "Last Expense of the month", status.HTTP_400_BAD_REQUEST)
        response = self.get_expense_with_response(status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_user_create_with_date_as_none_expenses(self):
        self.create_expense_with_response(250.5, None, 2, "Last Expense of the month", status.HTTP_400_BAD_REQUEST)
        response = self.get_expense_with_response(status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_user_create_with_category_id_as_none_expenses(self):
        self.create_expense_with_response(250.5, '2022-05-12', None, "Last Expense of the month", status.HTTP_400_BAD_REQUEST)
        response = self.get_expense_with_response(status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_user_create_with_name_as_none_expenses(self):
        self.create_expense_with_response(250.5, '2022-05-12', 2, None, status.HTTP_400_BAD_REQUEST)
        response = self.get_expense_with_response(status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_user_delete_created_expense(self):
        self.create_expense_with_response(
            250.5, '2021-01-30', 3, "Another expense", status.HTTP_201_CREATED)
        self.delete_expense_with_response(1, status.HTTP_200_OK)
        response = self.get_expense_with_response(status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_user_delete_inexistent_created_expense(self):
        self.delete_expense_with_response(4777, status.HTTP_400_BAD_REQUEST)
        response = self.get_expense_with_response(status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_user_cannot_delete_another_user_expense(self):
        another_user = User.objects.create(
            firebase_uid=create_random_string(FIREBASE_UID_LENGTH))
        Expense.create_expense_for_user(another_user, name='Random expense',
                                        date='2019-05-30', value=100, category=Category.objects.all()[1])

        self.delete_expense_with_response(1, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_modify_another_user_expense(self):
        another_user = User.objects.create(
            firebase_uid=create_random_string(FIREBASE_UID_LENGTH))
        Expense.create_expense_for_user(another_user, name='Random expense',
                                        date='2019-01-30', value=100, category=Category.objects.all()[1])
        self.patch_expense_with_response(
            1, 100, '2021-01-30', 1, 'Another Expense', status.HTTP_403_FORBIDDEN)

    def test_user_reads_expenses(self):
        self.create_expense_with_response(
            59999, '2021-03-25', 2, "Expensive Expense", status.HTTP_201_CREATED)
        response = self.get_expense_with_response(status.HTTP_200_OK)
        expense_json = response.json()[0]
        self.assertExpenseInformationIsRight(
            expense_json, 59999.0, '2021-03-25', 2, 'Expensive Expense', False)

    def test_user_update_all_information_related_to_category_expense(self):
        self.create_expense_with_response(
            250.5, '2021-01-30', 3, "Another Expense", status.HTTP_201_CREATED)
        self.patch_expense_with_response(
            1, 87444, '2020-02-05', 1, "Modified Expense", status.HTTP_200_OK)
        response = self.get_expense_with_response(status.HTTP_200_OK)

        expense_json = response.json()[0]
        self.assertExpenseInformationIsRight(
            expense_json, 87444.0, '2020-02-05', 1, 'Modified Expense', False)

    def test_user_cannot_update_future_expense_status_directly(self):
        self.create_expense_with_response(
            250.5, '2021-01-30', 3, "Another expense", status.HTTP_201_CREATED)

        response = self.client.patch(self.endpoint, {
            'id': 1,
            'value': 100,
            'date': '2021-01-30',
            'category_id': 1,
            'name': "Another expense",
            'future_expense': True
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.get_expense_with_response(status.HTTP_200_OK)

        expense_json = response.json()[0]

        self.assertExpenseInformationIsRight(
            expense_json, 100, '2021-01-30', 1, 'Another expense', False)

    def test_user_update_only_category_of_created_expense(self):
        self.create_expense_with_response(
            250.5, '2021-01-30', 3, "Another Expense", status.HTTP_201_CREATED)
        self.patch_expense_with_response(
            1, 250.5, '2021-01-30', 4, "Another Expense", status.HTTP_200_OK)
        response = self.get_expense_with_response(status.HTTP_200_OK)

        expense_json = response.json()[0]
        self.assertExpenseInformationIsRight(
            expense_json, 250.5, '2021-01-30', 4, "Another Expense", False)

    def test_user_update_only_value_of_created_expense(self):
        self.create_expense_with_response(
            250.5, '2021-01-30', 3, "Another Expense", status.HTTP_201_CREATED)
        self.patch_expense_with_response(
            1, 57778, '2021-01-30', 3, "Another Expense", status.HTTP_200_OK)
        response = self.get_expense_with_response(status.HTTP_200_OK)

        expense_json = response.json()[0]
        self.assertExpenseInformationIsRight(
            expense_json, 57778, '2021-01-30', 3, "Another Expense", False)

    def test_user_update_only_name_of_created_expense(self):
        self.create_expense_with_response(
            250.5, '2021-01-30', 3, "Another Expense", status.HTTP_201_CREATED)
        self.patch_expense_with_response(
            1, 250.5, '2021-01-30', 3, "Modified expense", status.HTTP_200_OK)
        response = self.get_expense_with_response(status.HTTP_200_OK)

        expense_json = response.json()[0]
        self.assertExpenseInformationIsRight(
            expense_json, 250.5, '2021-01-30', 3, "Modified expense", False)

    def test_user_update_only_date_of_created_expense(self):
        self.create_expense_with_response(
            250.5, '2021-01-30', 3, "Another Expense", status.HTTP_201_CREATED)
        self.patch_expense_with_response(
            1, 250.5, '2020-06-11', 3, "Another Expense", status.HTTP_200_OK)
        response = self.get_expense_with_response(status.HTTP_200_OK)

        expense_json = response.json()[0]
        self.assertExpenseInformationIsRight(
            expense_json, 250.5, '2020-06-11', 3, "Another Expense", False)

    def test_user_cannot_update_future_date(self):
        self.create_expense_with_response(
            250.5, '2021-01-30', 3, "Another Expense", status.HTTP_201_CREATED)
        self.patch_expense_with_response(
            1, 250.5, '2058-06-11', 3, "Another Expense", status.HTTP_400_BAD_REQUEST)
        response = self.get_expense_with_response(status.HTTP_200_OK)

        expense_json = response.json()[0]
        self.assertExpenseInformationIsRight(
            expense_json, 250.5, '2021-01-30', 3, "Another Expense", False)

    def test_user_cannot_update_future_date(self):
        self.create_expense_with_response(
            250.5, '2065-11-05', 3, "Another Expense", status.HTTP_400_BAD_REQUEST)
        response = self.get_expense_with_response(status.HTTP_200_OK)

        self.assertEqual(len(response.json()), 0)

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
        self.create_expense_with_response(10599, '2021-06-20', 1, "Another expense", status.HTTP_201_CREATED)
        self.create_expense_with_response(123456, '2022-06-02', 3, "Another expense", status.HTTP_201_CREATED)

        response = self.filter_expenses_with_response(["2022-06-02", "2022-06-02"], [], status.HTTP_200_OK)

        self.assertEqual(response.json()[0]['category']['id'], 3)

    def test_user_forgots_to_include_timeline_field(self):
        response = self.client.post(self.endpoint + "/filter", {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_reads_expenses_within_extended_time_line_and_several_categories(self):
        self.create_expense_with_response(10599, '2021-05-20', 1, "Very old expense", status.HTTP_201_CREATED)
        self.create_expense_with_response(123456, '2022-06-02', 3, "Another expense", status.HTTP_201_CREATED)

        response = self.client.post(self.endpoint + "/filter", {
            "timeline": ["2021-01-01", "2023-01-01"]
        }, format='json')

        response = self.filter_expenses_with_response(["2021-01-01", "2023-01-01"], [1,3], status.HTTP_200_OK)

        json_response_one = response.json()[0]
        json_response_two = response.json()[1]

        self.assertExpenseInformationIsRight(json_response_one, 10599, '2021-05-20', 1, "Very old expense", False)
        self.assertExpenseInformationIsRight(json_response_two, 123456, '2022-06-02', 3, "Another expense", False)

    def test_user_reads_expenses_within_extended_time_line_of_a_specific_category(self):
        self.create_expense_with_response(10599, '2021-05-20', 1, "Very old expense", status.HTTP_201_CREATED)
        self.create_expense_with_response(10500, '2021-12-30', 1, "Same category very old expense", status.HTTP_201_CREATED)
        self.create_expense_with_response(123456, '2022-06-02', 3, "Another expense", status.HTTP_201_CREATED)
        response = self.filter_expenses_with_response(["2021-01-01", "2023-01-01"], 1, status.HTTP_200_OK)

        self.assertEqual(len(response.json()), 2)

        json_response_one = response.json()[0]
        json_response_two = response.json()[1]

        self.assertExpenseInformationIsRight(
            json_response_one, 10500, '2021-12-30', 1, 'Same category very old expense', False)
        self.assertExpenseInformationIsRight(
            json_response_two, 10599, '2021-05-20', 1, 'Very old expense', False)


    def test_user_reads_expenses_within_extended_time_line_of_several_categories(self):
        self.create_expense_with_response(10599, '2021-05-20', 1, "Very old expense", status.HTTP_201_CREATED)
        self.create_expense_with_response(10500, '2021-12-30', 1, "Same category very old expense", status.HTTP_201_CREATED)
        self.create_expense_with_response(123456, '2022-06-02', 3, "Another expense", status.HTTP_201_CREATED)
        response = self.filter_expenses_with_response(["2021-01-01", "2023-01-01"], [1, 3], status.HTTP_200_OK)

        json_response_one = response.json()[0]
        json_response_two = response.json()[1]
        json_response_three = response.json()[2]

        self.assertExpenseInformationIsRight(
            json_response_one, 10500, '2021-12-30', 1, 'Same category very old expense', False)
        self.assertExpenseInformationIsRight(
            json_response_two, 10599, '2021-05-20', 1, 'Very old expense', False)
        self.assertExpenseInformationIsRight(
            json_response_three, 123456, '2022-06-02', 3, 'Another expense', False)

    def test_user_reads_expenses_within_an_invalid_time_line(self):
        self.filter_expenses_with_response(["2025-01-01", "2020-01-01"], [1, 3], status.HTTP_400_BAD_REQUEST)

    def test_user_has_no_provide_valid_token_to_add_expense(self):
        def action(self):
            return self.get_expense_with_response(status.HTTP_401_UNAUTHORIZED)

        response = self.assertActionInSecureEnvironment(action)
        self.assertEqual(response.json()['message'], 'A valid token was not provided')

    def test_user_has_no_provide_valid_token_to_read_expenses(self):
        def action(self):
            return self.create_expense_with_response(10500, '2021-12-30', 1, "A name", status.HTTP_401_UNAUTHORIZED)

        response = self.assertActionInSecureEnvironment(action)
        self.assertEqual(response.json()['message'], 'A valid token was not provided')

    def test_user_has_no_provide_valid_token_to_patch_expenses(self):
        def action(self):
            return self.patch_expense_with_response(155, 500, '2018-01-23', 4, "Another name", status.HTTP_401_UNAUTHORIZED)

        response = self.assertActionInSecureEnvironment(action)
        self.assertEqual(response.json()['message'], 'A valid token was not provided')

    def test_user_has_no_provide_valid_token_to_delete_expense(self):
        def action(self):
            return self.delete_expense_with_response(1110, status.HTTP_401_UNAUTHORIZED)

        response = self.assertActionInSecureEnvironment(action)
        self.assertEqual(response.json()['message'], 'A valid token was not provided')
