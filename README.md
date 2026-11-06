# Shift Manager Backend

This is my backend capstone project. A manager can create, view, edit, and delete shifts. Each shift belongs to the manager who made it. Other managers cannot access it.

User story: As a shift manager, I want to view my shifts so I can keep my schedule organized.

- Repo: https://github.com/Nightmare6998/shift-manager-backend
- Live API: https://shift-manager-backend-tdtl.onrender.com
- Health check: https://shift-manager-backend-tdtl.onrender.com/health

The project uses Python 3.12, Flask, SQLAlchemy, and JWT. Docker uses PostgreSQL. Running Python directly uses SQLite by default.

## Run with Docker

Install Python 3.12 and Docker Desktop. Start Docker Desktop. Clone this repo and open its folder:

```sh
git clone https://github.com/Nightmare6998/shift-manager-backend.git
cd shift-manager-backend
python scripts/setup_env.py
docker compose up -d --build
```

The setup script creates `.env` with random local secrets. Compose starts the app and database. Database migrations run at startup.

```sh
docker compose ps
curl -i http://localhost:5000/health
```

The health check should return `200` and `{"status":"ok"}`. In PowerShell, use `curl.exe` if needed.

To stop, run `docker compose down`. To start again, run `docker compose up -d`. The database keeps its data in a volume. Adding `-v` to the down command deletes that data.

## Run without Docker

```sh
python -m venv .venv
```

Activate it with `.venv\Scripts\Activate.ps1` on Windows or `source .venv/bin/activate` on macOS/Linux. Then run:

```sh
python -m pip install -r requirements.txt
python scripts/setup_env.py
python -m flask db upgrade
python -m flask run
```

## Settings

Real settings go in `.env`. Git ignores this file. `.env.example` shows which settings are needed.

| Setting | What it does |
| --- | --- |
| APP_ENV | Picks development, testing, or production |
| APP_NAME | Sets the app name |
| JWT_SECRET | Signs tokens; use a random value of at least 32 characters |
| JWT_ACCESS_TOKEN_EXPIRES_SECONDS | Sets how long tokens last; default is 3600 seconds |
| DATABASE_URL | Selects the database |
| POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB | Set up the local Docker database |
| PORT | Sets the hosting port; default is 5000 |

Compose uses `db` as the database host. Keep its database username, password, and database name to letters and numbers. The setup script handles the password. Use separate secrets for production, and never put real secrets in GitHub.

## API routes

Send JSON with `Content-Type: application/json`. Except for health, registration, and login, routes need an `Authorization: Bearer YOUR_TOKEN` header.

| Method | Route | Action | Success |
| --- | --- | --- | --- |
| GET | /health | Check the app | 200 |
| POST | /auth/register | Create an account | 201 |
| POST | /auth/login | Get a token | 200 |
| GET | /users/me | Read your profile | 200 |
| PATCH | /users/me | Change email or full_name | 200 |
| GET | /shifts | List your shifts | 200 |
| POST | /shifts | Create a shift | 201 |
| GET | /shifts/{id} | Read one shift | 200 |
| PUT | /shifts/{id} | Replace a shift | 200 |
| PATCH | /shifts/{id} | Change part of a shift | 200 |
| DELETE | /shifts/{id} | Delete a shift | 204 |
| GET | /admin/ping | Check admin access | 200 |

`GET /auth/me` and `GET /auth/profile` also read your profile. `PATCH /auth/profile` also updates it.

Errors have `error`, `message`, and `details` fields. Status codes are 400 for bad input, 401 for missing or bad login proof, 403 for a non-admin on the admin route, 404 for a missing shift, and 409 for an email already in use. Another manager's shift also returns 404 to keep it private. Admins can only access their own shifts too.

## Try it

These commands use Bash. Log in and copy the returned token into `YOUR_TOKEN`:

```sh
curl -i -X POST http://localhost:5000/auth/register -H 'Content-Type: application/json' -d '{"email":"manager@example.com","password":"password123"}'
curl -i -X POST http://localhost:5000/auth/login -H 'Content-Type: application/json' -d '{"email":"manager@example.com","password":"password123"}'
curl -i -X POST http://localhost:5000/shifts -H 'Authorization: Bearer YOUR_TOKEN' -H 'Content-Type: application/json' -d '{"role_title":"Floor lead","location":"Main store","start_time":"2026-12-01T08:00:00-06:00","end_time":"2026-12-01T16:00:00-06:00"}'
curl -i 'http://localhost:5000/shifts?page=1&per_page=2' -H 'Authorization: Bearer YOUR_TOKEN'
```

A shift needs role_title (up to 100 characters), location (up to 150), start_time, and end_time. Notes are optional (up to 5000 characters). Times must include a timezone, and end must come after start. The app returns times in UTC. The manager ID comes from the token.

PUT needs all four required fields and clears notes if left out. PATCH changes only the fields sent. DELETE returns an empty body. Profile changes only allow email and full_name. Passwords and hashes are never returned.

Lists return `data` and `meta`. Meta has page, per_page, total, and pages. Page defaults to 1; per_page defaults to 20 and must be 1–50. Results are ordered by ID. A page past the end returns an empty list with status 200. An empty collection has one empty page.

## Database and admin

Run `python -m flask db upgrade` to apply the included migrations. After a future model change, run `python -m flask db migrate -m "Describe the change"`, check the migration, then upgrade. Do not run `db init` again.

Create an admin from the terminal. It asks for a password:

```sh
docker compose exec web python -m flask create-admin --email admin@example.com
```

Without Docker, leave off `docker compose exec web`. Public registration always creates a normal user.

Passwords are saved as hashes. Login checks the hash and gives a signed JWT that expires. Logout deletes the token on the client. Since there is no token blacklist, logout does not cancel a token already issued.

## Tests

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
python scripts/smoke_test.py http://localhost:5000
```

The smoke test checks real HTTP requests with two test accounts. It hides tokens in its output. Save output with `python scripts/smoke_test.py http://localhost:5000 > evidence/local.txt`. Use the live URL to test deployment. GitHub also checks Docker startup and data after a restart.

## Deploy

Create a Render Docker web service from the public repo and a PostgreSQL database. Set APP_ENV to production, add a new JWT_SECRET, and set DATABASE_URL to the hosted database. Use the database provider's SSL settings. Set the health check path to `/health`. `start.sh` runs migrations and starts Gunicorn on the host's PORT. `render.yaml` has the basic settings too.

The current free API may take about a minute to wake up. Its free Render database expires on **December 6, 2026**. Move the data or upgrade before that date to keep it online. Review costs before choosing a paid plan.

If the app fails to start, check `docker compose logs web` or the hosting logs. Check the database URL and port. Inside Compose, use `db` for the database host, not `localhost`. The health route checks the app; the smoke test also checks database actions.

## Files

- `app/`: app factory, models, routes, and validation
- `migrations/`: database changes
- `scripts/`: local setup and smoke test
- `tests/`: API tests
- `docs/`: code notes and submission checklist

Read `docs/code-notes.md` to review how the code works and `docs/submission.md` before submitting.
