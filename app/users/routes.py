from flask import Blueprint, g, jsonify
from sqlalchemy.exc import IntegrityError
from app.auth.decorators import jwt_required
from app.errors import error_response
from app.extensions import db
from app.validation import account_fields, json_body

users_bp = Blueprint("users", __name__)


@users_bp.get("/users/me")
@users_bp.get("/auth/me")
@users_bp.get("/auth/profile")
@jwt_required
def get_profile():
    return jsonify(g.user.to_dict())


@users_bp.patch("/users/me")
@users_bp.patch("/auth/profile")
@jwt_required
def update_profile():
    # Only these two fields can change. Identity always comes from the token.
    values, errors = account_fields(json_body())
    if errors:
        return error_response(400, "validation_error", "Check your input.", errors)
    if not values:
        return error_response(400, "validation_error", "Include email or full_name.")
    for key, value in values.items():
        setattr(g.user, key, value)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error_response(409, "conflict", "Email is already registered")
    return jsonify(g.user.to_dict())
