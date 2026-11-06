# How the code works

- `app/__init__.py`: `create_app` builds the Flask app. It loads settings, starts extensions, and registers the blueprints.
- `config.py`: picks development, testing, or production settings. Secrets and the database URL come from the environment.
- `extensions.py`: holds the shared database and migration tools.
- `models/user.py`: stores accounts. Passwords are hashes, not readable passwords.
- `models/shift.py`: stores shifts. `user_id` points to the account that owns the shift. The relationship lets Python move from a user to their shifts and back.
- `auth/routes.py`: registration validates input and hashes the password. Login checks the hash and returns a signed token with an expiry.
- `auth/decorators.py`: checks the token before protected routes run. The admin check runs after login is verified.
- `users/routes.py`: reads the user from the token. Only email and full_name can change.
- `shifts/routes.py`: gets ownership from the token. Every read, change, and delete checks the owner. The list uses database limit and offset so it returns one page at a time.
- `validation.py`: checks inputs before saving anything. It converts times to UTC and checks that end is after start.
- `errors.py`: keeps errors in the same JSON format, including framework errors.
- `cli.py`: creates an admin from the terminal. The public registration route cannot create admins.
- `migrations/`: records database changes. Upgrade applies those changes to a new database.
- `start.sh`: applies migrations and starts Gunicorn. Compose waits for PostgreSQL to be ready first.

401 means login proof is missing or invalid. 403 means the user is logged in but lacks permission. A different manager gets 404 for your shifts so the API does not reveal which IDs belong to other people.

Docker keeps the app and its dependencies together. Compose runs the app and database together. The named volume keeps the database when containers stop.
