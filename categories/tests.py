import secrets

import hashlib
import hmac

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Category
from .serializers import CategorySerializer


class CategorySerializerTests(TestCase):
	def test_accepts_valid_category_data(self):
		serializer = CategorySerializer(
			data={'name': 'Books', 'description': 'Printed books'}
		)

		self.assertTrue(serializer.is_valid(), serializer.errors)
		category = serializer.save()
		self.assertEqual(category.name, 'Books')

	def test_name_is_required(self):
		serializer = CategorySerializer(data={'description': 'Printed books'})

		self.assertFalse(serializer.is_valid())
		self.assertIn('name', serializer.errors)


class CategoryViewSetTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		user = User.objects.create_user(username='api-user', password=secrets.token_urlsafe(32))
		token = Token.objects.create(user=user)
		self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

	def test_creates_and_lists_categories(self):
		response = self.client.post(
			'/api/categories/',
			{'name': 'Books', 'description': 'Printed books'},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(Category.objects.count(), 1)
		self.assertEqual(
			self.client.get('/api/categories/').data['results'][0]['name'],
			'Books',
		)

	def test_rejects_category_without_name(self):
		response = self.client.post('/api/categories/', {}, format='json')

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('name', response.data)

	def test_rejects_unauthenticated_request(self):
		response = APIClient().get('/api/categories/')

		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class HealthCheckTests(TestCase):
	def test_health_check_returns_ok(self):
		response = self.client.get('/health/')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.json(), {'status': 'ok'})

	def test_hello_world_page_is_available(self):
		response = self.client.get('/hello/')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertContains(response, 'Bookstore API is running')

	def test_webhook_rejects_invalid_signature(self):
		response = self.client.post(
			'/update_server/',
			data='{}',
			content_type='application/json',
			HTTP_X_HUB_SIGNATURE_256='sha256=invalid',
		)

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
