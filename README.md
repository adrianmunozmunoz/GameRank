# GameRank

A Django web application to browse, rate and comment on free-to-play video games.

I built it as the final project for a web applications course at Universidad Rey Juan Carlos (2024–2025). Demo video: [youtube.com/watch?v=6OCmZZMRA8s](https://www.youtube.com/watch?v=6OCmZZMRA8s)

## Features

- **Game catalogue** loaded from an XML listing, with the main page sorted by average user rating.
- **Game pages** with details, a 0–5 rating, follow button and comments.
- **Dynamic version with HTMX:** comments are loaded and posted without reloading the page, and comments can be liked or disliked in place.
- **User area:** summary of each user's ratings, comments and followed games, plus settings for alias, font and text size.
- **External APIs:** a page that merges the FreeToGame and MMOBomb public APIs into a single list, removes duplicates by title and filters by platform (PC or browser). In production it reads from local JSON backups instead of calling the APIs.
- **JSON endpoint** for each game (`/juego/<id>.json`).
- **Spanish and English interface**, chosen from the browser language.
- **Footer metrics** with totals for the site and the current user.
- **Django admin** for managing users and content.
- **15 automated tests** covering models, helper functions and views.

## Tech

Python · Django 5.1 · SQLite · HTMX · Bootstrap · Django i18n · REST APIs (`requests`)

## Data model

`Juego` (game) · `Valoracion` (rating, one per user and game) · `Comentario` (comment) · `VotoComentario` (like/dislike on a comment) · `Seguimiento` (followed game) · `ConfiguracionUsuario` (per-user display settings)

## Project structure

```
gamerank/              Main app: models, views, templates, tests
  management/commands/ importar_listado1: loads games from listado1.xml
gamerankproject/       Django settings and root URLs
data/                  Local JSON backups of the two external APIs
scripts/               Scripts to refresh those backups
locale/                English translations
static/, templates/    Shared static files, login and logout pages
listado1.xml           Game listing used to populate the database
```

## How to run it

Requires Python 3.10 or later.

```bash
git clone https://github.com/adrimm22/GameRank.git
cd GameRank
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py importar_listado1
python manage.py createsuperuser  # optional, to use /admin and log in
python manage.py runserver
```

Then open http://127.0.0.1:8000. To create regular users, use the admin site at `/admin`.

Run the tests with:

```bash
python manage.py test gamerank
```

## Configuration

Settings are read from environment variables, with defaults meant for local development:

| Variable               | Default                 |
|------------------------|-------------------------|
| `DJANGO_SECRET_KEY`    | development-only key    |
| `DJANGO_DEBUG`         | `True`                  |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1`   |

With `DJANGO_DEBUG=True` the API page calls FreeToGame and MMOBomb live; with `False` it uses the backups in `data/`.
