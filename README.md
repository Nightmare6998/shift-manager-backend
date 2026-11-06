# Shift Manager Backend

GitHub: https://github.com/Nightmare6998/shift-manager-backend

Live API: https://shift-manager-backend-tdtl.onrender.com

This API lets a shift manager create, view, change, and delete shifts. Each shift belongs to the manager who created it. Other managers cannot see or change it.

User story: As a shift manager, I want to view my shifts so I can keep the schedule organized.

Built with Python 3.12, Flask, SQLAlchemy, JWT, and PostgreSQL. Local Python setup uses SQLite. This is a backend only. It does not include employee accounts, automatic conflict checking, or a website.

## Run with Docker Compose

Install Python 3.12 and Docker Desktop. Start Docker Desktop before these steps.

Download this repo, open a terminal in its folder, then run:

```sh
python scripts/setup_env.py
docker compose up -d --build
```

The first command creates `.env` with random local secrets. The second starts the API and PostgreSQL. Migrations run before the API starts.

```sh
docker compose ps
curl -i http://localhost:5000/health
```

Expected: `200 OK` and `{"status":"ok"}`. In Windows PowerShell, use `curl.exe` if `curl` runs a different command.

To stop and restart:

```sh
docker compose down
docker compose up -d
```

Data stays in the `postgres_data` volume. `docker compose down -v` deletes it.

## Run without Docker

```sh
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

On macOS/Linux: `source .venv/bin/activate`.

```sh
python -m pip install -r requirements.txt
python scripts/setup_env.py
python -m flask db upgrade
python -m flask run
```

## Environment variables

`.env.example` shows the settings. Real values go in `.env`, which Git ignores.

| Variable | Purpose |
| --- | --- |
| APP_ENV | development, testing, or production |
| APP_NAME | App name; change it and restart to try config loading |
| JWT_SECRET | Random secret, at least 32 characters |
| JWT_ACCESS_TOKEN_EXPIRES_SECONDS | Token lifetime; default 3600 seconds |
| DATABASE_URL | SQLite locally or PostgreSQL on a host |
| POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB | Local Compose database settings |
| PORT | Hosting port; default 5000 |

Compose uses `db` as the database host. Use letters and numbers for its database username, password, and name. The setup script makes a safe random password. Production needs its own database URL and JWT secret. Never post real secrets in GitHub or school evidence.

## Endpoints

Send JSON with `Content-Type: application/json`. Protected routes need `Authorization: Bearer YOUR_TOKEN`.

| Method | Path | Purpose | Success |
| --- | --- | --- | --- |
| GET | /health | Check the API is running (public) | 200 |
| POST | /auth/register | Create an account (public) | 201 |
| POST | /auth/login | Get a token (public) | 200 |
| GET | /users/me | Read your profile | 200 |
| PATCH | /users/me | Change your email or full_name | 200 |
| GET | /shifts | List your shifts | 200 |
| POST | /shifts | Create your shift | 201 |
| GET | /shifts/{id} | Read your shift | 200 |
| PUT | /shifts/{id} | Replace your shift fields | 200 |
| PATCH | /shifts/{id} | Change part of your shift | 200 |
| DELETE | /shifts/{id} | Delete your shift | 204 |
| GET | /admin/ping | Check admin access | 200 |

`/auth/me` and `/auth/profile` also read your profile. `PATCH /auth/profile` also updates it. These keep the earlier lesson paths working.

Errors use the same shape: `{"error":"validation_error","message":"Check your input.","details":{}}`. Field errors appear in `details`.

| Status | Meaning |
| --- | --- |
| 400 | Bad JSON, missing fields, or invalid values |
| 401 | Missing, invalid, or expired token; incorrect login |
| 403 | Logged in, but not an admin on /admin/ping |
| 404 | Missing shift or a shift owned by another manager |
| 409 | Email is already registered |

The 404 ownership response keeps other managers' shift IDs private. Admins still only see their own shifts. Profiles never return passwords or password hashes. Profile updates only accept changes to email and full_name; other fields are ignored.

## Example requests

These examples use a Bash terminal. Replace `YOUR_TOKEN` with the login result.

```sh
curl -i -X POST http://localhost:5000/auth/register -H 'Content-Type: application/json' -d '{"email":"manager@example.com","password":"password123"}'
curl -i -X POST http://localhost:5000/auth/login -H 'Content-Type: application/json' -d '{"email":"manager@example.com","password":"password123"}'
curl -i -X POST http://localhost:5000/shifts -H 'Authorization: Bearer YOUR_TOKEN' -H 'Content-Type: application/json' -d '{"role_title":"Floor lead","start_time":"2026-12-01T08:00:00-06:00","end_time":"2026-12-01T16:00:00-06:00","location":"Main store","notes":"Opening shift"}'
curl -i 'http://localhost:5000/shifts?page=1&per_page=2' -H 'Authorization: Bearer YOUR_TOKEN'
```

Required shift fields: role_title (1–100 characters), location (1–150), start_time, and end_time. Notes are optional (up to 5000 characters). Times need an ISO timestamp with a timezone. End must be after start. Times are saved and returned in UTC. Ownership comes from the token, never the request body.

PUT requires all four required fields and clears notes if left out. PATCH changes only fields you send. DELETE returns an empty body.

Lists use `{"data":[...],"meta":{"page":1,"per_page":20,"total":1,"pages":1}}`. Page starts at 1. Per page defaults to 20 and must be 1–50. Results are ordered by ID. Pages past the end return an empty list with status 200. An empty collection has one empty page.

## Migrations and admin

Existing migrations are included. Apply them with `python -m flask db upgrade`. For future model changes, run `python -m flask db migrate -m "Describe the change"`, check the new file, then upgrade. Do not run `db init` again.

Create an admin privately; it asks for a password:

```sh
docker compose exec web python -m flask create-admin --email admin@example.com
```

Without Docker: `python -m flask create-admin --email admin@example.com`.

JWTs expire after the configured lifetime. Logout means deleting the token on the client. There is no session store or token blacklist, so logout does not cancel a token already issued. Roles are checked from the database after token verification.

## Tests and evidence

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
python scripts/smoke_test.py http://localhost:5000
```

The smoke test uses real HTTP requests and creates two temporary test accounts and shifts. It prints status codes and response bodies, with tokens hidden. Save text evidence with `python scripts/smoke_test.py http://localhost:5000 > evidence/local.txt`. Run it against the deployed URL for live evidence. See `docs/submission.md` for the last checks.

## Deployment

1. Push this project to a public GitHub repo.
2. Create a Render account and a PostgreSQL database (for example, Neon).
3. In Render, create a Docker web service from the repo. Set health check path to `/health`.
4. Set `APP_ENV=production`, a new random `JWT_SECRET`, and the host's `DATABASE_URL`. Use `postgresql+psycopg://...` and the provider's SSL settings (usually `sslmode=require`). Set the token lifetime to 3600.
5. Deploy. `start.sh` applies migrations, then runs Gunicorn on Render's `PORT`.
6. Run the smoke test against the live URL. Put the actual GitHub and live URLs in your submission.

`render.yaml` includes these service settings. Hosting may have a cost; review the plan before creating the service.

The current deployment uses free Render services. The API may take about a minute to wake up after being idle. Its free database expires on December 6, 2026. Move the data or upgrade the database before that date if the project still needs to stay online.

If startup fails, check `docker compose logs web` or the hosting logs. A database connection error often means a wrong URL, password, or host. Inside Compose, the database host is `db`, not `localhost`. A 502 from a host means to check startup logs and the port binding. `/health` checks that the API is running; the smoke test also checks database operations.

## Files

```text
app/          factory, models, validation, routes
migrations/   database changes
scripts/      setup and HTTP smoke test
tests/        API checks
docs/         short study notes and submission checklist
Dockerfile, docker-compose.yml, start.sh, render.yaml
```
