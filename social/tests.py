from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Post


class SocialApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.alice = User.objects.create_user(username='alice', password='alice-pass-123')
		self.bob = User.objects.create_user(username='bob', password='bob-pass-123')

	def authenticate_as(self, user):
		token, _ = Token.objects.get_or_create(user=user)
		self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

	def test_register_and_login_return_a_token(self):
		response = self.client.post(
			'/api/social/auth/register/',
			{'username': 'carol', 'password': 'carol-pass-123'},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertIn('token', response.data)

		response = self.client.post(
			'/api/social/auth/login/',
			{'username': 'carol', 'password': 'carol-pass-123'},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('token', response.data)

	def test_registration_rejects_a_common_password(self):
		response = self.client.post(
			'/api/social/auth/register/',
			{'username': 'weak-password-user', 'password': 'password123'},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('password', response.data)

	def test_social_home_page_is_available(self):
		response = self.client.get('/api/social/')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertContains(response, 'chirp.')

	def test_profile_can_be_updated_without_changing_all_fields(self):
		self.authenticate_as(self.alice)

		response = self.client.patch(
			'/api/social/profiles/me/',
			{
				'first_name': 'Alice',
				'password': 'new-alice-pass-123',
				'avatar': SimpleUploadedFile(
					'avatar.gif',
					b'GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;',
					content_type='image/gif',
				),
			},
			format='multipart',
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['first_name'], 'Alice')
		self.alice.refresh_from_db()
		self.assertTrue(self.alice.check_password('new-alice-pass-123'))
		self.assertTrue(self.alice.profile.avatar.name.startswith('avatars/avatar'))

	def test_following_user_populates_personalized_feed(self):
		post = Post.objects.create(author=self.bob, content='Hello from Bob')
		self.authenticate_as(self.alice)

		self.assertEqual(self.client.get('/api/social/posts/feed/').data['count'], 0)
		response = self.client.post(
			f'/api/social/profiles/{self.bob.profile.id}/follow/',
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)

		response = self.client.get('/api/social/posts/feed/')
		self.assertEqual(response.data['count'], 1)
		self.assertEqual(response.data['results'][0]['id'], post.id)

		self.assertEqual(
			self.client.get(
				f'/api/social/profiles/{self.alice.profile.id}/following/'
			).data[0]['username'],
			'bob',
		)
		self.assertEqual(
			self.client.get(
				f'/api/social/profiles/{self.bob.profile.id}/followers/'
			).data[0]['username'],
			'alice',
		)

		self.assertTrue(
			self.client.get(f'/api/social/profiles/{self.bob.profile.id}/').data['is_following']
		)
		response = self.client.post(
			f'/api/social/profiles/{self.bob.profile.id}/unfollow/',
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertFalse(
			self.client.get(f'/api/social/profiles/{self.bob.profile.id}/').data['is_following']
		)

	def test_posts_can_be_filtered_by_author_before_pagination(self):
		for number in range(3):
			Post.objects.create(author=self.alice, content=f'Alice post {number}')
		Post.objects.create(author=self.bob, content='Bob post')

		response = self.client.get('/api/social/posts/?author=alice')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['count'], 3)
		self.assertTrue(all(post['author'] == 'alice' for post in response.data['results']))

	def test_profile_lookup_accepts_username_with_period(self):
		user = User.objects.create_user(username='ana.costa', password='ana-pass-123')

		response = self.client.get('/api/social/profiles/by-username/ana.costa/')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['username'], user.username)

	def test_user_can_like_and_comment_on_a_post(self):
		post = Post.objects.create(author=self.bob, content='A post to interact with')
		self.authenticate_as(self.alice)

		response = self.client.post(f'/api/social/posts/{post.id}/like/', format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['likes_count'], 1)
		self.assertTrue(self.client.get(f'/api/social/posts/{post.id}/').data['is_liked'])
		response = self.client.delete(f'/api/social/posts/{post.id}/unlike/')
		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
		self.assertFalse(self.client.get(f'/api/social/posts/{post.id}/').data['is_liked'])

		response = self.client.post(
			f'/api/social/posts/{post.id}/comments/',
			{'content': 'Great post!'},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data['author'], 'alice')

	def test_posts_and_comments_reject_whitespace_only_content(self):
		post = Post.objects.create(author=self.bob, content='A post to validate')
		self.authenticate_as(self.alice)

		post_response = self.client.post('/api/social/posts/', {'content': '   '}, format='json')
		comment_response = self.client.post(
			f'/api/social/posts/{post.id}/comments/',
			{'content': '   '},
			format='json',
		)

		self.assertEqual(post_response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('content', post_response.data)
		self.assertEqual(comment_response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('content', comment_response.data)

	def test_only_author_can_update_post_and_anonymous_requests_are_rejected(self):
		post = Post.objects.create(author=self.bob, content='Private editing')

		self.assertEqual(
			self.client.post('/api/social/posts/', {'content': 'No access'}, format='json').status_code,
			status.HTTP_401_UNAUTHORIZED,
		)

		self.authenticate_as(self.alice)
		response = self.client.patch(
			f'/api/social/posts/{post.id}/',
			{'content': 'Trying to edit'},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

# Create your tests here.
