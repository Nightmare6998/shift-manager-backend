import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models import User
from app.validation import account_fields


@click.command("create-admin")
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@with_appcontext
def create_admin(email, password):
    values, errors = account_fields({"email": email, "password": password}, registration=True)
    if errors:
        raise click.ClickException(str(errors))
    if db.session.scalar(db.select(User).where(User.email == values["email"])):
        raise click.ClickException("Email is already registered.")
    user = User(email=values["email"], password_hash=generate_password_hash(password), role="admin")
    db.session.add(user)
    db.session.commit()
    click.echo("Admin account created.")
