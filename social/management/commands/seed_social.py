from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from social.models import Comment, Post


class Command(BaseCommand):
	help = 'Creates a reusable demo population for Chirp.'

	people = (
		('ana.costa', 'Ana', 'Costa', 47),
		('bruno.lima', 'Bruno', 'Lima', 12),
		('carla.mendes', 'Carla', 'Mendes', 32),
		('diego.santos', 'Diego', 'Santos', 15),
		('elisa.rocha', 'Elisa', 'Rocha', 44),
		('felipe.alves', 'Felipe', 'Alves', 53),
		('giulia.nunes', 'Giulia', 'Nunes', 49),
		('henrique.melo', 'Henrique', 'Melo', 68),
	)

	posts = (
		('ana.costa', 'Comecando a semana com cafe, ideias novas e uma lista possivel de tarefas.'),
		('bruno.lima', 'Acabei de terminar um livro excelente. Aceito recomendacoes para o proximo.'),
		('carla.mendes', 'Pequenas pausas tambem fazem parte de um bom dia de trabalho.'),
		('diego.santos', 'Alguem mais animado para aprender uma tecnologia nova esta semana?'),
		('elisa.rocha', 'Minha receita de hoje: massa, legumes assados e zero pressa.'),
		('felipe.alves', 'O sol apareceu por aqui. Hora perfeita para uma caminhada curta.'),
		('giulia.nunes', 'Organizei minhas referencias de design e estou cheia de ideias.'),
		('henrique.melo', 'Qual foi a melhor coisa que voce aprendeu este mes?'),
		('ana.costa', 'Compartilhar uma ideia inacabada pode ser o primeiro passo para melhora-la.'),
		('carla.mendes', 'Hoje escolhi fazer uma coisa por vez. Surpreendentemente funciona.'),
	)

	connections = {
		'ana.costa': ('bruno.lima', 'carla.mendes', 'giulia.nunes'),
		'bruno.lima': ('ana.costa', 'diego.santos', 'henrique.melo'),
		'carla.mendes': ('ana.costa', 'elisa.rocha', 'felipe.alves'),
		'diego.santos': ('bruno.lima', 'giulia.nunes'),
		'elisa.rocha': ('ana.costa', 'carla.mendes', 'henrique.melo'),
		'felipe.alves': ('bruno.lima', 'elisa.rocha'),
		'giulia.nunes': ('ana.costa', 'diego.santos', 'henrique.melo'),
		'henrique.melo': ('bruno.lima', 'carla.mendes'),
	}

	comments = (
		('ana.costa', 'Que comeco bom de semana!'),
		('giulia.nunes', 'Uma lista possivel e meu tipo favorito de lista.'),
		('elisa.rocha', 'Quero saber qual foi o livro.'),
		('diego.santos', 'Estou nessa. Qual tecnologia voce escolheu?'),
		('felipe.alves', 'Caminhada curta melhora qualquer tarde.'),
	)

	def handle(self, *args, **options):
		users = {}
		for username, first_name, last_name, avatar_number in self.people:
			user, created = User.objects.get_or_create(
				username=username,
				defaults={'first_name': first_name, 'last_name': last_name},
			)
			if created:
				user.set_password('demo-social-2026')
				user.save()
			profile = user.profile
			profile.avatar_url = f'https://i.pravatar.cc/300?img={avatar_number}'
			profile.save(update_fields=('avatar_url',))
			users[username] = user

		for username, followed_usernames in self.connections.items():
			users[username].profile.following.set(
				users[followed_username].profile for followed_username in followed_usernames
			)

		posts = []
		for username, content in self.posts:
			post, _ = Post.objects.get_or_create(author=users[username], content=content)
			posts.append(post)

		for index, post in enumerate(posts):
			post.likes.add(users[self.people[(index + 1) % len(self.people)][0]])
			post.likes.add(users[self.people[(index + 3) % len(self.people)][0]])

		for index, (username, content) in enumerate(self.comments):
			Comment.objects.get_or_create(post=posts[index], author=users[username], content=content)

		self.stdout.write(self.style.SUCCESS('Demo population is ready: 8 profiles, 10 posts, likes, comments, and follows.'))