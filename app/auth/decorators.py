from functools import wraps
import jwt
from flask import current_app, g, request
from app.errors import error_response
from app.extensions import db
from app.models import User


def jwt_required(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header:
            return error_response(401, "authentication_error", "Missing token")
        parts = header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return error_response(401, "authentication_error", "Invalid token")
        try:
            payload = jwt.decode(parts[1], current_app.config["JWT_SECRET"], algorithms=["HS256"],
                                 options={"require": ["sub", "iat", "exp"]})
            g.user = db.session.get(User, int(payload["sub"]))
            if g.user is None:
                raise ValueError()
        except jwt.ExpiredSignatureError:
            return error_response(401, "authentication_error", "Token expired")
        except (jwt.InvalidTokenError, ValueError, TypeError):
            return error_response(401, "authentication_error", "Invalid token")
        g.user_id = g.user.id
        return function(*args, **kwargs)
    return wrapped


def admin_required(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        if g.user.role != "admin":
            return error_response(403, "authorization_error", "Admin access required")
        return function(*args, **kwargs)
    return wrapped
