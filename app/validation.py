import re
from datetime import datetime, timezone
from flask import request
from werkzeug.exceptions import BadRequest


def json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        raise BadRequest("Send a non-empty JSON object.")
    return data


def account_fields(data, registration=False):
    values, errors = {}, {}
    if registration or "email" in data:
        email = data.get("email")
        if not isinstance(email, str) or len(email) > 255 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email.strip()):
            errors["email"] = "Enter a valid email, up to 255 characters."
        else:
            values["email"] = email.strip().lower()
    if registration:
        password = data.get("password")
        if not isinstance(password, str) or not 8 <= len(password) <= 128:
            errors["password"] = "Use 8 to 128 characters."
        else:
            values["password"] = password
    if "full_name" in data:
        name = data["full_name"]
        if name is not None and (not isinstance(name, str) or len(name.strip()) > 100):
            errors["full_name"] = "Use text up to 100 characters, or null."
        else:
            values["full_name"] = name.strip() if name is not None else None
    return values, errors


def shift_fields(data, existing=None, partial=False):
    values, errors = {}, {}
    required = {"role_title", "location", "start_time", "end_time"}
    allowed = required | {"notes"}
    for key in data.keys() - allowed:
        errors[key] = "This field cannot be set."
    for key in required:
        if key not in data and not partial:
            errors[key] = "This field is required."
    for key, limit in (("role_title", 100), ("location", 150)):
        if key in data:
            value = data[key]
            if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
                errors[key] = f"Use non-empty text up to {limit} characters."
            else:
                values[key] = value.strip()
    for key in ("start_time", "end_time"):
        if key in data:
            try:
                value = datetime.fromisoformat(data[key].replace("Z", "+00:00"))
                if value.tzinfo is None:
                    raise ValueError()
                values[key] = value.astimezone(timezone.utc)
            except (AttributeError, TypeError, ValueError, OverflowError):
                errors[key] = "Use an ISO timestamp with a timezone."
    if "notes" in data:
        if data["notes"] is not None and (not isinstance(data["notes"], str) or len(data["notes"]) > 5000):
            errors["notes"] = "Use text up to 5000 characters, or null."
        else:
            values["notes"] = data["notes"]
    if existing:
        start = values.get("start_time", existing.start_time.replace(tzinfo=timezone.utc))
        end = values.get("end_time", existing.end_time.replace(tzinfo=timezone.utc))
    else:
        start, end = values.get("start_time"), values.get("end_time")
    if start and end and end <= start:
        errors["end_time"] = "End time must be after start time."
    if partial and not values and not errors:
        errors["body"] = "Include at least one shift field."
    if not partial:
        values.setdefault("notes", None)
    return values, errors
