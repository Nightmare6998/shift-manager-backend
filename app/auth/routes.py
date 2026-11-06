from datetime import datetime, timedelta, timezone
import jwt
from flask import Blueprint, current_app, jsonify
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
from app.errors import error_response
from app.extensions import db
from app.models import User
from app.validation import account_fields, json_body

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/register")
def register():
    data = json_body()
    values, errors = account_fields(data, registration=True)
    allowed_fields = {"email", "password", "full_name"}
    for key in data:
        if key not in allowed_fields:
            errors[key] = "This field cannot be set."
    if errors:
        return error_response(400, "validation_error", "Check your input.", errors)
    password = values.pop("password")
    user = User(
        email=values["email"],
        full_name=values.get("full_name"),
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error_response(409, "conflict", "Email is already registered")
    return jsonify(user.to_dict()), 201


@auth_bp.post("/login")
def login():
    data = json_body()
    email = data.get("email")
    password = data.get("password")
    if not isinstance(email, str) or not isinstance(password, str) or not email or not password or len(password) > 128:
        return error_response(400, "validation_error", "Email and password are required.")
    user = User.query.filter_by(email=email.strip().lower()).first()
    if not user or not check_password_hash(user.password_hash, password):
        return error_response(401, "authentication_error", "Invalid credentials")
    now = datetime.now(timezone.utc)
    lifetime = current_app.config["JWT_ACCESS_TOKEN_EXPIRES_SECONDS"]
    payload = {
        "sub": str(user.id),
        "iat": now,
        "exp": now + timedelta(seconds=lifetime),
    }
    token = jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")
    return jsonify(access_token=token, token_type="Bearer", expires_in=lifetime)
