# Social API

Clone social construído com Django REST Framework para o Projeto Final da EBAC.

## Links da Entrega

- Repositório: https://github.com/RodrigoRiRocha/projeto-final-ebac
- Aplicação em produção: https://twitter-clone-ebac.vercel.app/api/social/
- Health check: https://twitter-clone-ebac.vercel.app/health/

## Recursos

- Cadastro e login com token.
- Perfil editável com nome, senha e URL de avatar opcionais.
- Seguir e deixar de seguir perfis.
- Feed formado apenas por publicações de perfis seguidos.
- CRUD de postagens, curtidas e comentários.
- Paginação, autenticação por token, Docker Compose e GitHub Actions.

## Execução local

```powershell
py -m pip install -r requirements.txt
py manage.py migrate
py manage.py runserver
```

Abra `http://127.0.0.1:8000/api/social/` para usar a interface web do clone social.

Para executar com Docker Compose:

```powershell
docker compose up --build
```

## Deploy na Vercel

O projeto inclui `vercel.json` e o entrypoint `api/index.py`. Configure as variáveis
abaixo na Vercel antes do deploy de produção:

```text
DJANGO_SECRET_KEY=<chave-secreta>
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=.vercel.app
DATABASE_URL=<url-postgresql>
DJANGO_CSRF_TRUSTED_ORIGINS=https://seu-projeto.vercel.app
DJANGO_SMTP_HOST=<host-smtp>
DJANGO_SMTP_PORT=587
DJANGO_SMTP_USERNAME=<usuario-smtp>
DJANGO_SMTP_PASSWORD=<senha-smtp>
DJANGO_SMTP_USE_TLS=true
```

Use PostgreSQL em produção. O SQLite é mantido apenas para desenvolvimento local e não
persiste com segurança em funções serverless.

Use uma chave aleatória longa para `DJANGO_SECRET_KEY` (por exemplo, gerada por
`py -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`).
Execute `py manage.py migrate` antes do deploy sempre que existirem novas migrations.
O entrypoint serverless não executa migrations durante requisições da aplicação.

## Autenticação

Crie uma conta em `POST /api/social/auth/register/` ou faça login em
`POST /api/social/auth/login/`. Nas rotas protegidas, envie o cabeçalho:

```text
Authorization: Token <seu_token>
```

## Principais endpoints

| Método | Endpoint | Descrição |
| --- | --- | --- |
| POST | `/api/social/auth/register/` | Cria uma conta e retorna um token. |
| POST | `/api/social/auth/login/` | Autentica uma conta e retorna um token. |
| GET/PATCH | `/api/social/profiles/me/` | Consulta ou atualiza o próprio perfil. |
| POST | `/api/social/profiles/<id>/follow/` | Segue um perfil. |
| POST | `/api/social/profiles/<id>/unfollow/` | Deixa de seguir um perfil. |
| GET | `/api/social/posts/feed/` | Exibe o feed personalizado. |
| GET/POST | `/api/social/posts/` | Lista ou cria postagens. |
| PATCH/DELETE | `/api/social/posts/<id>/` | Altera ou remove a própria postagem. |
| POST | `/api/social/posts/<id>/like/` | Curte uma postagem. |
| DELETE | `/api/social/posts/<id>/unlike/` | Remove uma curtida. |
| POST | `/api/social/posts/<id>/comments/` | Adiciona um comentário. |

## Testes

```powershell
py manage.py test
```