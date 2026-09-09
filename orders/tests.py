import secrets

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from categories.models import Category
from products.models import Product

from .serializers import OrderSerializer


class OrderSerializerTests(TestCase):
	def setUp(self):
		category = Category.objects.create(name='Books')
		self.product = Product.objects.create(
			name='Clean Code',
			price='79.90',
			category=category,
		)

	def test_creates_order_with_products(self):
		serializer = OrderSerializer(
			data={'customer_name': 'Ada Lovelace', 'products': [self.product.id]}
		)

		self.assertTrue(serializer.is_valid(), serializer.errors)
		order = serializer.save()
		self.assertEqual(order.customer_name, 'Ada Lovelace')
		self.assertEqual(list(order.products.all()), [self.product])
		self.assertIn('created_at', OrderSerializer(order).data)

	def test_rejects_unknown_product(self):
		serializer = OrderSerializer(
			data={'customer_name': 'Ada Lovelace', 'products': [999]}
		)

		self.assertFalse(serializer.is_valid())
		self.assertIn('products', serializer.errors)


class OrderViewSetTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		user = User.objects.create_user(username='api-user', password=secrets.token_urlsafe(32))
		token = Token.objects.create(user=user)
		self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
		category = Category.objects.create(name='Books')
		self.product = Product.objects.create(
			name='Clean Code',
			price='79.90',
			category=category,
		)

	def test_creates_order_and_deletes_it(self):
		response = self.client.post(
			'/api/orders/',
			{'customer_name': 'Ada Lovelace', 'products': [self.product.id]},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data['products'], [self.product.id])

		response = self.client.delete(f"/api/orders/{response.data['id']}/")
		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

	def test_rejects_order_with_unknown_product(self):
		response = self.client.post(
			'/api/orders/',
			{'customer_name': 'Ada Lovelace', 'products': [999]},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('products', response.data)
