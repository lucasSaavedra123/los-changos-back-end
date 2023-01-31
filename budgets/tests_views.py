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


class TestBudgetsView(APITestCase):
    def assertActionInSecureEnvironment(self, action):
        os.environ["ENVIRONMENT"] = "PROD"
        return_element = action(self)
        os.environ["ENVIRONMENT"] = "DEV"
        return return_element

    def setUp(self):
        self.endpoint = '/budget'

    def delete_category_with_response(self, id, expected_status_code):
        response = self.client.delete(
            self.endpoint, {'id': str(id)}, format='json')

        self.assertEqual(response.status_code, expected_status_code)

        return response

    def create_a_budget_with_response(self, initial_date, final_date, details, expected_status_code):
        response = self.client.post(self.endpoint, {
            'initial_date': initial_date,
            'final_date': final_date,
            'details': details
        }, format='json')

        self.assertEqual(response.status_code, expected_status_code)

        return response

    def patch_a_budget_with_response(self, id, initial_date, final_date, details, expected_status_code):
        response = self.client.patch(self.endpoint, {
            'id': id,
            'initial_date': initial_date,
            'final_date': final_date,
            'details': details
        }, format='json')

        self.assertEqual(response.status_code, expected_status_code)

        return response

    def get_budget_with_response(self, expected_status_code):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, expected_status_code)

        return response

    def make_future_expense_in_budget_with_response(self, future_expense_id, expense_done_date, expected_status_code):
        response = self.client.patch(
            self.endpoint + '/expended', {
                'future_expense_id': future_expense_id,
                'expense_done_date': expense_done_date
        }, format='json')

        self.assertEqual(response.status_code, expected_status_code)

        return response

    def test_create_one_budget_with_one_limit_detail_for_user(self):
        self.create_a_budget_with_response('2023-05-01', '2024-06-01', [{
            'category_id': 1,
            'limit': 5000
        }], status.HTTP_201_CREATED)

    def test_create_one_budget_with_one_future_expense_detail_for_user(self):
        self.create_a_budget_with_response('2023-05-01', '2024-06-01', [
            {
                'category_id': 1,
                'value': 5000,
                'expiration_date': '2023-11-05',
                'name': 'AySa Bill'
            }
        ], status.HTTP_201_CREATED)

    def test_create_one_budget_with_one_future_expense_but_fails_because_detail_is_out_of_budget_dates(self):
        self.create_a_budget_with_response('2023-05-01', '2024-06-01', [
            {
                'category_id': 1,
                'value': 5000,
                'expiration_date': '2021-11-05',
                'name': 'AySa Bill'
            }
        ], status.HTTP_400_BAD_REQUEST)

        self.create_a_budget_with_response('2023-05-01', '2024-06-01', [
            {
                'category_id': 1,
                'value': 5000,
                'expiration_date': '2029-03-01',
                'name': 'AySa Bill'
            }
        ], status.HTTP_400_BAD_REQUEST)

    def test_create_one_budget_with_one_future_expense_and_user_execute_payment(self):
        self.create_a_budget_with_response('2022-01-01', '2024-06-01', [
            {
                'category_id': 1,
                'value': 5000,
                'expiration_date': '2023-12-05',
                'name': 'AySa Bill'
            }
        ], status.HTTP_201_CREATED)

        self.make_future_expense_in_budget_with_response(1, '2023-01-12', status.HTTP_200_OK)

    def test_user_execute_payment_but_has_no_current_budget(self):
        self.make_future_expense_in_budget_with_response(1, '2023-01-12', status.HTTP_400_BAD_REQUEST)

    def test_create_one_budget_but_execute_an_inexistent_detail(self):
        self.create_a_budget_with_response('2022-01-01', '2024-06-01', [
            {
                'category_id': 1,
                'value': 5000,
                'expiration_date': '2023-12-05',
                'name': 'AySa Bill'
            }
        ], status.HTTP_201_CREATED)

        self.make_future_expense_in_budget_with_response(15, '2023-01-12', status.HTTP_400_BAD_REQUEST)

    def test_create_one_budget_with_details_for_user_and_he_retrieve_it(self):
        self.create_a_budget_with_response('2023-05-01', '2024-06-01', [
            {
                'category_id': 1,
                'limit': 5000
            },
            {
                'category_id': 1,
                'value': 4000,
                'expiration_date': '2023-11-05',
                'name': 'AySa Bill'
            }
        ], status.HTTP_201_CREATED)

        response = self.get_budget_with_response(status.HTTP_200_OK)

        self.assertEqual(len(response.json()), 1)

        first_budget = response.json()[0]

        self.assertEqual(first_budget['initial_date'], '2023-05-01')
        self.assertEqual(first_budget['final_date'], '2024-06-01')
        self.assertEqual(len(first_budget['details']), 6)

    def test_create_one_budget_but_one_field_is_not_included(self):
        response = self.client.post(self.endpoint, {
            'initial_date': '2023-05-01',
            'final_date': '2029-06-01',
            'details': [
                {
                    'category_id': 1,
                }
            ]
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_creates_two_budgets_with_different_details_for_user_and_then_he_retrieve_them(self):
        self.create_a_budget_with_response('2023-05-01', '2023-06-01', [
            {
                'category_id': 1,
                'limit': 5000
            }
        ], status.HTTP_201_CREATED)

        self.create_a_budget_with_response('2023-01-01', '2023-02-01', [
            {
                'category_id': 3,
                'limit': 1500
            },
            {
                'category_id': 2,
                'limit': 5000
            }
        ], status.HTTP_201_CREATED)

        response = self.get_budget_with_response(status.HTTP_200_OK)

        self.assertEqual(len(response.json()), 2)

        first_budget = response.json()[0]

        self.assertEqual(len(first_budget['details']), 5)

    def test_user_creates_a_budget_and_then_he_modifies_it(self):
        self.create_a_budget_with_response('2030-02-01', '2050-02-01', [
            {
                'category_id': 3,
                'limit': 1500
            },
            {
                'category_id': 2,
                'limit': 5000
            }
        ], status.HTTP_201_CREATED)

        response = self.patch_a_budget_with_response(1, '2021-01-01', '2024-02-01', [
            {
                'category_id': 1,
                'limit': 1000
            },
            {
                'category_id': 3,
                'value': 2000,
                'name': 'AySa Bill',
                'expiration_date': '2023-12-05'
            }
        ], status.HTTP_200_OK)

        response = self.get_budget_with_response(status.HTTP_200_OK)

        response = response.json()[0]

        self.assertEqual(response['id'], 1)
        self.assertEqual(response['initial_date'], '2021-01-01')
        self.assertEqual(response['editable'], False)
        self.assertEqual(response['final_date'], '2024-02-01')
        self.assertEqual(response['details'][0]['category']['id'], 1)
        self.assertEqual(response['details'][0]['limit'], 1000.00)
        self.assertEqual(response['details'][1]['category']['id'], 3)
        self.assertEqual(response['details'][1]['value'], 2000.00)

    def test_user_creates_an_budget_with_limit_id_that_does_not_exist(self):
        self.create_a_budget_with_response('2020-02-01', '2050-02-01', [
            {
                'category_id': 310,
                'limit': 1500
            }
        ], status.HTTP_400_BAD_REQUEST)

    def test_user_creates_an_active_budget_and_then_he_tries_to_modify_it_but_fails(self):
        self.create_a_budget_with_response('2020-02-01', '2050-02-01', [
            {
                'category_id': 3,
                'limit': 1500
            },
            {
                'category_id': 2,
                'limit': 5000
            }
        ], status.HTTP_201_CREATED)

        self.patch_a_budget_with_response(1, '2021-01-01', '2023-02-01', [
            {
                'category_id': 1,
                'limit': 1000
            },
            {
                'category_id': 3,
                'limit': 2000
            }
        ], status.HTTP_400_BAD_REQUEST)

    def test_user_deletes_own_budget(self):
        self.create_a_budget_with_response('2023-05-01', '2023-06-01', [
            {
                'category_id': 1,
                'limit': 5000
            }
        ], status.HTTP_201_CREATED)

        self.create_a_budget_with_response('2023-01-01', '2050-02-01', [
            {
                'category_id': 3,
                'limit': 1500
            },
            {
                'category_id': 2,
                'limit': 5000
            }
        ], status.HTTP_201_CREATED)

        self.delete_category_with_response(1, status.HTTP_200_OK)

        response = self.client.get(self.endpoint)

        self.assertEqual(len(response.json()), 1)

    def test_user_deletes_an_innexistent_budget(self):
        self.delete_category_with_response(577, status.HTTP_400_BAD_REQUEST)

    def test_user_cannot_delete_own_current_budget(self):
        self.create_a_budget_with_response('2020-05-01', '2030-06-01', [
            {
                'category_id': 1,
                'limit': 5000
            }
        ], status.HTTP_201_CREATED)

        self.delete_category_with_response(1, status.HTTP_400_BAD_REQUEST)

    def test_user_cannot_delete_another_user_budget(self):
        another_user = User.objects.create(
            firebase_uid=create_random_string(FIREBASE_UID_LENGTH))

        Budget.objects.create(
            user=another_user, initial_date='2020-01-01', final_date='2025-01-01')

        self.delete_category_with_response(1, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_update_another_user_budget(self):
        another_user = User.objects.create(
            firebase_uid=create_random_string(FIREBASE_UID_LENGTH))

        Budget.objects.create(
            user=another_user, initial_date='2020-01-01', final_date='2025-01-01')

        self.patch_a_budget_with_response(1, '2023-01-01', '2023-02-01', [
            {
                'category_id': 1,
                'limit': 1000
            },
            {
                'category_id': 3,
                'limit': 2000
            }
        ], status.HTTP_403_FORBIDDEN)

    def test_user_has_no_provide_valid_token_to_read_budgets(self):
        def action(self):
            return self.get_budget_with_response(status.HTTP_401_UNAUTHORIZED)

        self.assertActionInSecureEnvironment(action)

    def test_user_has_no_provide_valid_token_to_add_budgets(self):
        def action(self):
            return self.create_a_budget_with_response('2023-01-01', '2023-02-01', [
                {
                    'category_id': 1,
                    'limit': 1000
                },
                {
                    'category_id': 3,
                    'limit': 2000
                }
            ], status.HTTP_401_UNAUTHORIZED)

        self.assertActionInSecureEnvironment(action)

    def test_user_has_no_provide_valid_token_to_patch_budget(self):
        def action(self):
            return self.patch_a_budget_with_response(1, '2023-01-01', '2023-02-01', [
                {
                    'category_id': 1,
                    'limit': 1000
                },
                {
                    'category_id': 3,
                    'limit': 2000
                }
            ], status.HTTP_401_UNAUTHORIZED)

        self.assertActionInSecureEnvironment(action)

    def test_user_has_no_provide_valid_token_to_delete_budget(self):
        def action(self):
            return self.delete_category_with_response(99, status.HTTP_401_UNAUTHORIZED)

        self.assertActionInSecureEnvironment(action)

    def test_user_get_current_budget(self):
        self.create_a_budget_with_response('2020-01-01', '2023-02-01', [
                {
                    'category_id': 1,
                    'limit': 1000
                },
                {
                    'category_id': 3,
                    'limit': 2000
                }
            ], status.HTTP_201_CREATED)

        response = self.client.get(self.endpoint + '/current')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = response.json()

        self.assertEqual(response['id'], 1)
        self.assertEqual(response['initial_date'], '2020-01-01')
        self.assertEqual(response['final_date'], '2023-02-01')
        self.assertEqual(response['details'][0]['category']['id'], 1)
        self.assertEqual(response['details'][0]['limit'], 1000.00)
        self.assertEqual(response['details'][1]['category']['id'], 3)
        self.assertEqual(response['details'][1]['limit'], 2000.00)

    def test_user_get_no_current_budget(self):
        self.create_a_budget_with_response('2030-01-01', '2050-02-01', [
                {
                    'category_id': 4,
                    'limit': 9778
                },
                {
                    'category_id': 2,
                    'limit': 1000
                }
            ], status.HTTP_201_CREATED)

        response = self.client.get(self.endpoint + '/current')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = response.json()

        self.assertEqual(response, {})
