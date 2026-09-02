from django.contrib.auth import authenticate
from django.contrib.staticfiles import finders
from django.http import FileResponse, Http404
from django.shortcuts import render
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .models import Post, Profile
from .pagination import SocialPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import CommentSerializer, PostSerializer, ProfileSerializer, RegisterSerializer


def social_home(request):
	return render(request, 'social/home.html')


def explore(request):
	return render(request, 'social/explore.html')


def profile_page(request, username):
	return render(request, 'social/profile.html', {'username': username})


def settings_page(request):
	return render(request, 'social/settings.html')


def asset(request, filename):
	if filename not in {'app.css', 'app.js'}:
		raise Http404
    
	path = finders.find(f'social/{filename}')
	if not path:
		raise Http404
	content_type = 'text/css' if filename.endswith('.css') else 'application/javascript'
	return FileResponse(open(path, 'rb'), content_type=content_type)


class RegisterView(APIView):
	permission_classes = (AllowAny,)
	throttle_scope = 'auth'

	def post(self, request):
		serializer = RegisterSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user = serializer.save()
		token, _ = Token.objects.get_or_create(user=user)
		return Response({'token': token.key}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
	permission_classes = (AllowAny,)

	throttle_scope = 'auth'

	def post(self, request):
		user = authenticate(
			username=request.data.get('username'),
			password=request.data.get('password'),
		)
		if user is None:
			return Response(
				{'detail': 'Invalid username or password.'},
				status=status.HTTP_400_BAD_REQUEST,
			)
		token, _ = Token.objects.get_or_create(user=user)
		return Response({'token': token.key})


class ProfileViewSet(ReadOnlyModelViewSet):
	queryset = Profile.objects.select_related('user')
	serializer_class = ProfileSerializer
	permission_classes = (AllowAny,)
	pagination_class = SocialPagination

	@action(detail=False, methods=('get',), url_path='by-username/(?P<username>[^/]+)')
	def by_username(self, request, username=None):
		profile = self.get_queryset().get(user__username=username)
		return Response(self.get_serializer(profile).data)

	@action(detail=False, methods=('get', 'patch'), permission_classes=(IsAuthenticated,))
	def me(self, request):
		profile = request.user.profile
		if request.method == 'PATCH':
			serializer = self.get_serializer(profile, data=request.data, partial=True)
			serializer.is_valid(raise_exception=True)
			serializer.save()
			return Response(serializer.data)
		return Response(self.get_serializer(profile).data)

	@action(detail=True, methods=('post',), permission_classes=(IsAuthenticated,))
	def follow(self, request, pk=None):
		profile = self.get_object()
		if profile == request.user.profile:
			return Response(
				{'detail': 'You cannot follow yourself.'},
				status=status.HTTP_400_BAD_REQUEST,
			)
		request.user.profile.following.add(profile)
		return Response({'status': 'following'})

	@action(detail=True, methods=('post',), permission_classes=(IsAuthenticated,))
	def unfollow(self, request, pk=None):
		request.user.profile.following.remove(self.get_object())
		return Response({'status': 'unfollowed'})

	@action(detail=True, methods=('get',), permission_classes=(IsAuthenticated,))
	def following(self, request, pk=None):
		profile = self.get_object()
		return Response(self.get_serializer(profile.following.order_by('user__username'), many=True).data)

	@action(detail=True, methods=('get',), permission_classes=(IsAuthenticated,))
	def followers(self, request, pk=None):
		profile = self.get_object()
		return Response(self.get_serializer(profile.followers.order_by('user__username'), many=True).data)


class PostViewSet(ModelViewSet):
	queryset = Post.objects.select_related('author__profile').prefetch_related(
		'likes', 'comments__author__profile'
	)
	serializer_class = PostSerializer
	permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
	pagination_class = SocialPagination

	def get_queryset(self):
		queryset = super().get_queryset()
		author = self.request.query_params.get('author')
		if author:
			queryset = queryset.filter(author__username=author)
		return queryset

	def perform_create(self, serializer):
		serializer.save(author=self.request.user)

	@action(detail=False, methods=('get',), permission_classes=(IsAuthenticated,))
	def feed(self, request):
		following = request.user.profile.following.all()
		queryset = self.get_queryset().filter(author__profile__in=following)
		page = self.paginate_queryset(queryset)
		if page is not None:
			return self.get_paginated_response(self.get_serializer(page, many=True).data)
		return Response(self.get_serializer(queryset, many=True).data)

	@action(detail=True, methods=('post',), permission_classes=(IsAuthenticated,))
	def like(self, request, pk=None):
		post = self.get_object()
		post.likes.add(request.user)
		return Response({'likes_count': post.likes.count()})

	@action(detail=True, methods=('delete',), permission_classes=(IsAuthenticated,))
	def unlike(self, request, pk=None):
		post = self.get_object()
		post.likes.remove(request.user)
		return Response(status=status.HTTP_204_NO_CONTENT)

	@action(detail=True, methods=('post',), permission_classes=(IsAuthenticated,))
	def comments(self, request, pk=None):
		serializer = CommentSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		comment = serializer.save(post=self.get_object(), author=request.user)
		return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)

# Create your views here.
