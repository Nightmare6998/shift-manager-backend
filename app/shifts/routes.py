import math
from flask import Blueprint, g, jsonify, request
from app.auth.decorators import jwt_required
from app.errors import error_response
from app.extensions import db
from app.models import Shift
from app.validation import json_body, shift_fields

shifts_bp = Blueprint("shifts", __name__, url_prefix="/shifts")


def owned_shift(shift_id):
    # Other managers get the same 404 as a missing record.
    return db.session.scalar(db.select(Shift).where(Shift.id == shift_id, Shift.user_id == g.user_id))


@shifts_bp.get("")
@jwt_required
def list_shifts():
    try:
        page = int(request.args.get("page", "1"))
        per_page = int(request.args.get("per_page", "20"))
        if page < 1 or page > 2147483647 or not 1 <= per_page <= 50:
            raise ValueError()
    except ValueError:
        return error_response(400, "validation_error", "page must be positive; per_page must be 1 to 50.")
    query = Shift.query.filter_by(user_id=g.user_id)
    total = query.count()
    shifts = query.order_by(Shift.id.asc()).offset((page - 1) * per_page).limit(per_page).all()
    return jsonify(data=[shift.to_dict() for shift in shifts],
                   meta={"page": page, "per_page": per_page, "total": total,
                         "pages": max(1, math.ceil(total / per_page))})


@shifts_bp.post("")
@jwt_required
def create_shift():
    values, errors = shift_fields(json_body())
    if errors:
        return error_response(400, "validation_error", "Check your input.", errors)
    shift = Shift(user_id=g.user_id, **values)
    db.session.add(shift)
    db.session.commit()
    return jsonify(shift.to_dict()), 201


@shifts_bp.get("/<int:shift_id>")
@jwt_required
def get_shift(shift_id):
    shift = owned_shift(shift_id)
    if shift is None:
        return error_response(404, "not_found", "Shift not found")
    return jsonify(shift.to_dict())


@shifts_bp.route("/<int:shift_id>", methods=["PUT", "PATCH"])
@jwt_required
def update_shift(shift_id):
    shift = owned_shift(shift_id)
    if shift is None:
        return error_response(404, "not_found", "Shift not found")
    values, errors = shift_fields(json_body(), existing=shift, partial=request.method == "PATCH")
    if errors:
        return error_response(400, "validation_error", "Check your input.", errors)
    for key, value in values.items():
        setattr(shift, key, value)
    db.session.commit()
    return jsonify(shift.to_dict())


@shifts_bp.delete("/<int:shift_id>")
@jwt_required
def delete_shift(shift_id):
    shift = owned_shift(shift_id)
    if shift is None:
        return error_response(404, "not_found", "Shift not found")
    db.session.delete(shift)
    db.session.commit()
    return "", 204
