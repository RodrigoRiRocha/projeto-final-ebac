from django.contrib import admin

from .models import Comment, Post, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'following_total', 'followers_total')
	search_fields = ('user__username', 'user__first_name', 'user__last_name')

	@admin.display(description='Seguindo')
	def following_total(self, profile):
		return profile.following.count()

	@admin.display(description='Seguidores')
	def followers_total(self, profile):
		return profile.followers.count()


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
	list_display = ('author', 'short_content', 'created_at', 'likes_total')
	list_filter = ('created_at',)
	search_fields = ('content', 'author__username')
	readonly_fields = ('created_at', 'updated_at')

	@admin.display(description='Postagem')
	def short_content(self, post):
		return post.content[:80]

	@admin.display(description='Curtidas')
	def likes_total(self, post):
		return post.likes.count()


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
	list_display = ('author', 'short_content', 'post', 'created_at')
	list_filter = ('created_at',)
	search_fields = ('content', 'author__username', 'post__content')
	readonly_fields = ('created_at',)

	@admin.display(description='Comentário')
	def short_content(self, comment):
		return comment.content[:80]
