import os

from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from categories.models import Category
from users.constants import FIREBASE_UID_LENGTH
from utils import create_random_string
from users.models import User


# Create your tests here.
class TestCategoriesView(APITestCase):
    def assertActionInSecureEnvironment(self, action):
        os.environ["ENVIRONMENT"] = "PROD"
        return_element = action(self)
        os.environ["ENVIRONMENT"] = "DEV"
        return return_element

    def create_category_with_response(self, name, material_ui_icon_name, expected_status_code):
        response = self.client.post(self.endpoint, {
            'name': name,
            'material_ui_icon_name': material_ui_icon_name
        }, format='json')

        self.assertEqual(response.status_code, expected_status_code)

        return response

    def get_category_with_response(self, expected_status_code):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, expected_status_code)

        return response

    def delete_category_with_response(self, id, expected_status_code):
        response = self.client.delete(self.endpoint, {'id': str(id)}, format='json')

        self.assertEqual(response.status_code, expected_status_code)

        return response

    def patch_category_with_response(self, id, name, material_ui_icon_name, expected_status_code):
        response = self.client.patch(self.endpoint, {
            'id': id,
            'name': name,
            'material_ui_icon_name': material_ui_icon_name
        }, format='json')

        self.assertEqual(response.status_code, expected_status_code)

        return response

    def setUp(self):
        self.endpoint = '/category'
        self.static_categories_as_dict = [
            {'id': 1, 'material_ui_icon_name': 'AccountBalance',
                'static': True, 'name': 'Impuestos Y Servicios', 'color': 'rgba(0,255,255,1)'},
            {'id': 2, 'material_ui_icon_name': 'Casino',
                'static': True, 'name': 'Entretenimiento Y Ocio', 'color': 'rgba(0,255,0,1)'},
            {'id': 3, 'material_ui_icon_name': 'Home',
                'static': True, 'name': 'Hogar Y Mercado', 'color': 'rgba(0,255,124,1)'},
            {'id': 4, 'material_ui_icon_name': 'EmojiEmotions',
                'static': True, 'name': 'Buen Vivir/Antojos', 'color': 'rgba(255,0,0,1)'},
            {'id': 5, 'material_ui_icon_name': 'Kitchen',
                'static': True, 'name': 'Electrodomesticos', 'color': 'rgba(255,0,255,1)'}
        ]

    def test_user_create_a_category(self):
        self.create_category_with_response('Cellphone Accesories', 'SettingsCellRounded', status.HTTP_201_CREATED)
        response = self.get_category_with_response(status.HTTP_200_OK)
        category_with_id_six = [category for category in response.json() if category['id'] == 6]
        self.assertEqual(len(category_with_id_six), 1)

    def test_user_delete_created_category(self):
        self.create_category_with_response('Flights', 'AirplanemodeActiveRounded', status.HTTP_201_CREATED)
        self.delete_category_with_response(6, status.HTTP_200_OK)
        response = self.get_category_with_response(status.HTTP_200_OK)

        category_with_id_six = [category for category in response.json() if category['id'] == 6]
        self.assertEqual(len(category_with_id_six), 0)
        self.assertEqual(response.json(), self.static_categories_as_dict)

    def test_user_cannot_delete_another_user_category(self):
        another_user = User.objects.create(firebase_uid=create_random_string(FIREBASE_UID_LENGTH))
        Category.create_category_for_user(another_user, name='Random category', material_ui_icon_name='ShuffleRounded')
        self.delete_category_with_response(6, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_modify_another_user_category(self):
        another_user = User.objects.create(firebase_uid=create_random_string(FIREBASE_UID_LENGTH))
        Category.create_category_for_user(another_user, name='Random category', material_ui_icon_name='ShuffleRounded')
        self.patch_category_with_response(6, 'Your category was modifed', 'ShuffleRounded', status.HTTP_403_FORBIDDEN)

    def test_user_reads_categories(self):
        self.create_category_with_response('Custom Category', 'BorderColor', status.HTTP_201_CREATED)
        json_response = self.get_category_with_response(status.HTTP_200_OK).json()

        expected_json_response = self.static_categories_as_dict + \
            [
                {
                    'id': 6,
                    'material_ui_icon_name': 'BorderColor',
                    'static': False,
                    'name': 'Custom Category',
                    'color': Category.objects.get(id=6).color
                }
            ]

        self.assertEqual(json_response, expected_json_response)

    def test_user_update_all_information_related_to_created_category(self):
        self.create_category_with_response('Custom Category', 'BorderColor', status.HTTP_201_CREATED)
        self.patch_category_with_response(6, 'Energy', 'Bolt', status.HTTP_200_OK)
        json_response = self.get_category_with_response(status.HTTP_200_OK).json()

        expected_json_response = self.static_categories_as_dict + \
            [
                {
                    'id': 6,
                    'material_ui_icon_name': 'Bolt',
                    'static': False,
                    'name': 'Energy',
                    'color': Category.objects.get(id=6).color
                }
            ]

        self.assertEqual(json_response, expected_json_response)

    def test_user_update_only_name_of_created_category(self):
        self.create_category_with_response('Custom Category', 'BorderColor', status.HTTP_201_CREATED)
        self.patch_category_with_response(6, 'Another Name For Custom Category', 'BorderColor', status.HTTP_200_OK)
        json_response = self.get_category_with_response(status.HTTP_200_OK).json()

        expected_json_response = self.static_categories_as_dict + \
            [
                {
                    'id': 6,
                    'material_ui_icon_name': 'BorderColor',
                    'static': False,
                    'name': 'Another Name For Custom Category',
                    'color': Category.objects.get(id=6).color
                }
            ]

        self.assertEqual(json_response, expected_json_response)

    def test_user_update_only_icon_of_created_category(self):
        self.create_category_with_response('Custom Category', 'BorderColor', status.HTTP_201_CREATED)
        self.patch_category_with_response(6, 'Custom Category', 'Bolt', status.HTTP_200_OK)
        json_response = self.get_category_with_response(status.HTTP_200_OK).json()

        expected_json_response = self.static_categories_as_dict + \
            [
                {
                    'id': 6,
                    'material_ui_icon_name': 'Bolt',
                    'static': False,
                    'name': 'Custom Category',
                    'color': Category.objects.get(id=6).color
                }
            ]

        self.assertEqual(json_response, expected_json_response)

    def test_user_forgots_to_include_field_in_create_request(self):
        response = self.client.post(self.endpoint, {'name': 'Custom Category'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_forgots_to_include_field_in_patch_request(self):
        response = self.client.patch(self.endpoint, {'name': 'Custom Category','material_ui_icon_name': 'Bolt'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_include_category_name_as_none_in_create_request(self):
        response = self.client.post(self.endpoint, {'name': None, 'material_ui_icon_name': 'Bolt'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_include_category_icon_as_none_in_create_request(self):
        response = self.client.post(self.endpoint, {'name': 'Custom Category', 'material_ui_icon_name': None}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_include_category_name_as_none_in_patch_request(self):
        self.create_category_with_response('Custom Category', "Bolt", status.HTTP_201_CREATED)
        response = self.client.patch(self.endpoint, {'id': 6, 'name': None, 'material_ui_icon_name': 'Bolt'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_include_category_icon_as_none_in_patch_request(self):
        self.create_category_with_response('Custom Category', "Bolt", status.HTTP_201_CREATED)
        response = self.client.patch(self.endpoint, {'id': 6, 'name': 'Custom Category', 'material_ui_icon_name': None}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_include_non_existent_id_in_patch_request(self):
        response = self.client.patch(self.endpoint, {'id': 788, 'name': 'Custom Category', 'material_ui_icon_name': 'Bolt'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_has_no_provide_valid_token_to_read_categories(self):        
        def action(self):
            return self.get_category_with_response(status.HTTP_401_UNAUTHORIZED)

        response = self.assertActionInSecureEnvironment(action)

    def test_user_has_no_provide_valid_token_to_add_category(self):
        def action(self):
            return self.create_category_with_response('Custom Category', 'BorderColor', status.HTTP_401_UNAUTHORIZED)

        response = self.assertActionInSecureEnvironment(action)

    def test_user_has_no_provide_valid_token_to_patch_category(self):
        def action(self):
            return self.patch_category_with_response(7, 'Custom Category', 'BorderColor', status.HTTP_401_UNAUTHORIZED)

        response = self.assertActionInSecureEnvironment(action)

    def test_user_has_no_provide_valid_token_to_delete_category(self):
        def action(self):
            return self.delete_category_with_response(85, status.HTTP_401_UNAUTHORIZED)

        response = self.assertActionInSecureEnvironment(action)
