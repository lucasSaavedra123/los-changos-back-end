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
class TestCategoriesModel(TestCase):

    def setUp(self):
        self.a_user = User.objects.create(firebase_uid=create_random_string(FIREBASE_UID_LENGTH))
        self.category_created = Category.objects.create(user=self.a_user, name='Education', material_ui_icon_name='School')

    def test_category_is_created_for_user(self):
        self.assertEqual(len(Category.categories_from_user(self.a_user)), 6)

    def test_category_from_user_is_deleted(self):
        self.category_created.delete()
        self.assertEqual(len(Category.categories_from_user(self.a_user)), 5)

    def test_created_category_is_not_static(self):
        self.assertFalse(self.category_created.static)

    def test_two_categories_with_same_name_should_not_be_created_for_a_user(self):
        with self.assertRaises(ValidationError):
            Category.objects.create(user=self.a_user, name='Education', material_ui_icon_name='Car')

    def test_category_dictionary_serialization(self):
        self.assertEqual(self.category_created.as_dict['id'], self.category_created.id)
        self.assertEqual(self.category_created.as_dict['name'],  'Education')
        self.assertEqual(self.category_created.as_dict['material_ui_icon_name'], 'School')
        self.assertFalse(self.category_created.as_dict['static'])
        self.assertEqual(self.category_created.as_dict['color'], self.category_created.color)

class TestCategoriesView(APITestCase):
    def assertActionInSecureEnvironment(self, action):
        os.environ["ENVIRONMENT"] = "PROD"
        self.assertEqual(action(self).status_code, status.HTTP_401_UNAUTHORIZED)
        os.environ["ENVIRONMENT"] = "DEV"

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

    def test_user_creates_categories(self):
        response = self.client.post(self.endpoint, {
            'name': 'Cellphone Accesories',
            'material_ui_icon_name': 'Apple'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_delete_created_category(self):
        response = self.client.post(self.endpoint, {
            'name': 'Cellphone Accesories',
            'material_ui_icon_name': 'Apple'
        }, format='json')

        response = self.client.delete(self.endpoint, {'id': '6'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.json(), self.static_categories_as_dict)

    def test_user_cannot_delete_another_user_category(self):
        another_user = User.objects.create(firebase_uid=create_random_string(FIREBASE_UID_LENGTH))

        Category.create_category_for_user(another_user, name='Random category', material_ui_icon_name='Apple')

        response = self.client.delete(self.endpoint, {'id': '6'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_modify_another_user_category(self):
        another_user = User.objects.create(firebase_uid=create_random_string(FIREBASE_UID_LENGTH))

        Category.create_category_for_user(another_user, name='Random category', material_ui_icon_name='Apple')

        response = self.client.patch(self.endpoint, {'id': 6, 'name': 'Your category was modifed', 'material_ui_icon_name': 'Apple'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_reads_categories(self):
        self.client.post(self.endpoint, {
            'name': 'Custom Category',
            'material_ui_icon_name': 'BorderColor'
        }, format='json')

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_response = self.static_categories_as_dict + \
            [{'id': 6, 'material_ui_icon_name': 'BorderColor',
                'static': False, 'name': 'Custom Category', 'color': Category.objects.get(id=6).color}]

        self.assertEqual(response.json(), expected_response)

    def test_user_update_all_information_related_to_created_category(self):
        self.client.post(self.endpoint, {
            'name': 'Custom Category',
            'material_ui_icon_name': 'BorderColor'
        }, format='json')

        self.client.patch(self.endpoint, {
            'id': 6,
            'name': 'Energy',
            'material_ui_icon_name': 'Bolt'
        }, format='json')

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_response = self.static_categories_as_dict + \
            [{'id': 6, 'material_ui_icon_name': 'Bolt',
                'static': False, 'name': 'Energy', 'color': Category.objects.get(id=6).color}]

        self.assertEqual(response.json(), expected_response)

    def test_user_update_only_name_of_created_category(self):
        self.client.post(self.endpoint, {
            'name': 'Custom Category',
            'material_ui_icon_name': 'BorderColor'
        }, format='json')

        self.client.patch(self.endpoint, {
            'id': 6,
            'name': 'Another category name',
            'material_ui_icon_name': 'BorderColor'
        }, format='json')

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_response = self.static_categories_as_dict + \
            [{'id': 6, 'material_ui_icon_name': 'BorderColor',
                'static': False, 'name': 'Another Category Name', 'color': Category.objects.get(id=6).color}]

        self.assertEqual(response.json(), expected_response)

    def test_user_update_only_icon_of_created_category(self):
        response = self.client.post(self.endpoint, {
            'name': 'Custom Category',
            'material_ui_icon_name': 'BorderColor'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.patch(self.endpoint, {
            'id': 6,
            'name': 'Custom Category',
            'material_ui_icon_name': 'Bolt'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_response = self.static_categories_as_dict + \
            [{'id': 6, 'material_ui_icon_name': 'Bolt',
                'static': False, 'name': 'Custom Category', 'color': Category.objects.get(id=6).color}]

        self.assertEqual(response.json(), expected_response)

    def test_user_forgots_to_include_field_in_create_request(self):
        response = self.client.post(self.endpoint, {
            'name': 'Custom Category',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_forgots_to_include_field_in_patch_request(self):
        response = self.client.patch(self.endpoint, {
            'name': 'Custom Category',
            'material_ui_icon_name': 'Bolt'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_has_no_provide_valid_token_to_read_categories(self):        
        def action(self):
            return self.client.get(self.endpoint)

        self.assertActionInSecureEnvironment(action)

    def test_user_has_no_provide_valid_token_to_add_category(self):
        def action(self):
            return self.client.post(self.endpoint, {'name': 'Custom Category', 'material_ui_icon_name': 'BorderColor'}, format='json')

        self.assertActionInSecureEnvironment(action)

    def test_user_has_no_provide_valid_token_to_patch_category(self):
        def action(self):
            return self.client.patch(self.endpoint, {'id': 7, 'name': 'Custom Category', 'material_ui_icon_name': 'BorderColor'}, format='json')

        self.assertActionInSecureEnvironment(action)

    def test_user_has_no_provide_valid_token_to_delete_category(self):
        def action(self):
            return self.client.delete(self.endpoint, {'id': 85}, format='json')

        self.assertActionInSecureEnvironment(action)

