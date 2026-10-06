# GameRank

A Django web application to browse, rate and comment on free-to-play video games. Final project for a web applications course at Universidad Rey Juan Carlos (2024-2025).

## Details

* Name: Adrián Muñoz
* Degree: Telecommunication Engineering
* Basic features video (url): https://www.youtube.com/watch?v=6OCmZZMRA8s
* Optional features video (url): https://www.youtube.com/watch?v=VhpBB2SarOY
* Passwords: juan/arjona1234 maria/ismav1234 guille/llermo4567

## Core features

GameRank is a platform to browse, rate and comment on video games. Its main features are:

- Main list of games sorted by average rating, so the best-rated ones are easy to find.

- Detail page for each game with image, description, technical information, a 0 to 5 rating and comments sorted by date.

- Dynamic version built with HTMX, which loads and posts comments without reloading the page.

- User authentication, so each user can rate, comment on and follow games and save their preferences.

- Personal page with a summary of the user's ratings, comments and followed games.

- Bootstrap interface with options to change the font and text size.

- Django Admin Site to manage users and content.

- Footer metrics with the total number of games and comments, and the current user's activity.

- JSON resource for each game (`/juego/<id>.json`).

- Help page explaining how the application works.

## Optional features

* "Like / Dislike" on comments:
  - Users can vote on other users' comments. It works with HTMX, so the counter updates instantly without reloading the page.
* Custom favicon:
  - The application has its own icon in the browser tab.
* Integration with two public APIs (FreeToGame and MMOBomb):
  - One view merges the games from both APIs into a single list.
  - Duplicates are removed by comparing titles, so each game appears only once.
  - Games can be filtered by platform (PC or browser).
  - In development (`DEBUG=True`) the data is downloaded live; in production (`DEBUG=False`) it uses copies stored in `data/`, because the hosting server did not allow requests to external URLs.
* Internationalisation:
  - The interface is shown in Spanish or English depending on the browser language. All texts are marked and translated with `makemessages` and `compilemessages`.
* Automated tests:
  - 15 tests covering the main model methods (such as `puntuacion_media` or `num_likes`), helper functions (`comentarios_con_votos`) and edge cases, such as preventing empty comments.

## How to run it

Requires Python 3.10 or later. The repository includes a sample database with 78 games, comments, ratings and the test users above.

```bash
git clone https://github.com/adrianmunozmunoz/GameRank.git
cd GameRank
python -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver
```

The application will be available at http://127.0.0.1:8000.

To start with an empty database, delete `db.sqlite3` and run:

```bash
python manage.py migrate
python manage.py importar_listado1
python manage.py createsuperuser
```

To run the tests:

```bash
python manage.py test gamerank
```

## Configuration

Settings are read from environment variables. If they are not set, defaults meant for local development are used:

| Variable               | Default                     |
|------------------------|-----------------------------|
| `DJANGO_SECRET_KEY`    | development-only key        |
| `DJANGO_DEBUG`         | `True`                      |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1`       |
