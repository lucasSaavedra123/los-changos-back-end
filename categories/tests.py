from django.test import TestCase
from categories.models import Category
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from users.constants import FIREBASE_UID_LENGTH
from utils import create_random_string
from users.models import User
from django.core.exceptions import ValidationError


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
            Category.objects.create(user=self.a_user, name='eDucatioN', material_ui_icon_name='Car')

    def test_category_dictionary_serialization(self):
        self.assertDictEqual(self.category_created.as_dict,{
                'id': self.category_created.id,
                'name': 'education',
                'material_ui_icon_name': 'School',
                'static': False
            })


class TestCategoriesView(APITestCase):
    def setUp(self):
        self.endpoint = '/category'
        self.static_categories_as_dict =  [
            {'id': 1, 'material_ui_icon_name': 'AccountBalance', 'static': True, 'name': 'impuestos y servicios'},
            {'id': 2, 'material_ui_icon_name': 'Casino', 'static': True, 'name': 'entretenimiento y ocio'},
            {'id': 3, 'material_ui_icon_name': 'Home', 'static': True, 'name': 'hogar y mercado'},
            {'id': 4, 'material_ui_icon_name': 'EmojiEmotions', 'static': True, 'name': 'buen vivir/antojos'},
            {'id': 5, 'material_ui_icon_name': 'Kitchen', 'static': True, 'name': 'electrodomesticos'}
        ]

    def test_user_creates_categories(self):
        response = self.client.post(self.endpoint, {
            'name': 'Cellphone Accesories',
            'material_ui_icon_name': 'Apple'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_reads_categories(self):
        self.client.post(self.endpoint, {
            'name': 'Custom Category',
            'material_ui_icon_name': 'BorderColor'
        }, format='json')

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_response = self.static_categories_as_dict + [{'id': 6, 'material_ui_icon_name': 'BorderColor', 'static': False, 'name': 'custom category'}]

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

        expected_response = self.static_categories_as_dict + [{'id': 6, 'material_ui_icon_name': 'Bolt', 'static': False, 'name': 'energy'}]

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

        expected_response = self.static_categories_as_dict + [{'id': 6, 'material_ui_icon_name': 'BorderColor', 'static': False, 'name': 'another category name'}]

        self.assertEqual(response.json(), expected_response)

    def test_user_update_only_icon_of_created_category(self):
        response = self.client.post(self.endpoint, {
            'name': 'Custom Category',
            'material_ui_icon_name': 'BorderColor'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.patch(self.endpoint, {
            'id': 6,
            'name':'Custom Category',
            'material_ui_icon_name': 'Bolt'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_response = self.static_categories_as_dict + [{'id': 6, 'material_ui_icon_name': 'Bolt', 'static': False, 'name': 'custom category'}]

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
