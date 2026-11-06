from flask import Blueprint, jsonify
from app.auth.decorators import admin_required, jwt_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/ping")
@jwt_required
@admin_required
def admin_ping():
    return jsonify(status="ok", message="Admin privileges verified")
