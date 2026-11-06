from datetime import datetime, timedelta, timezone
import jwt
import pytest
from flask_migrate import upgrade
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash
from app import create_app
from app.extensions import db
from app.models import Shift, User


@pytest.fixture()
def app():
    app = create_app("testing")
    with app.app_context():
        upgrade()
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture()
def client(app):
    return app.test_client()


def account(client, email="a@example.com"):
    assert client.post("/auth/register", json={"email": email, "password": "password123"}).status_code == 201
    response = client.post("/auth/login", json={"email": email, "password": "password123"})
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json["access_token"]}


def shift_data(**changes):
    data = {"role_title": "Floor lead", "location": "Main store",
            "start_time": "2026-12-01T08:00:00-06:00", "end_time": "2026-12-01T16:00:00-06:00",
            "notes": "Opening shift"}
    data.update(changes)
    return data


def test_registration_hash_and_duplicate(app, client):
    response = client.post("/auth/register", json={"email": "A@example.com", "password": "password123"})
    assert response.status_code == 201
    assert set(response.json) == {"id", "email", "full_name", "created_at"}
    with app.app_context():
        user = db.session.get(User, response.json["id"])
        assert user.password_hash.startswith("scrypt:")
        assert check_password_hash(user.password_hash, "password123")
        assert user.role == "user"
    assert client.post("/auth/register", json={"email": "a@example.com", "password": "password123"}).status_code == 409


@pytest.mark.parametrize("body", [{}, [], None, {"email": 5}, {"email": "bad", "password": "short"},
                                   {"email": "a@example.com", "password": "password123", "role": "admin"}])
def test_registration_rejects_bad_input(client, body):
    response = client.post("/auth/register", json=body)
    assert response.status_code == 400
    assert set(response.json) == {"error", "message", "details"}


def test_login_generic_failure(client):
    account(client)
    wrong_password = client.post("/auth/login", json={"email": "a@example.com", "password": "wrong"})
    unknown_email = client.post("/auth/login", json={"email": "unknown@example.com", "password": "wrong"})
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json == unknown_email.json


def test_profile_identity_and_allowlist(app, client):
    a, b = account(client), account(client, "b@example.com")
    response = client.patch("/users/me", headers=a,
                            json={"full_name": "Alice", "role": "admin", "password_hash": "bad", "id": 2})
    assert response.status_code == 200
    assert response.json["email"] == "a@example.com"
    assert client.get("/users/me", headers=b).json["full_name"] is None
    assert client.get("/auth/me", headers=a).json == response.json
    with app.app_context():
        user = db.session.get(User, response.json["id"])
        assert user.role == "user" and check_password_hash(user.password_hash, "password123")
    assert client.patch("/users/me", headers=a, json={"email": "b@example.com"}).status_code == 409


def test_crud_and_ownership(client):
    a, b = account(client), account(client, "b@example.com")
    created = client.post("/shifts", headers=a, json=shift_data())
    assert created.status_code == 201
    assert created.json["start_time"] == "2026-12-01T14:00:00+00:00"
    path = f'/shifts/{created.json["id"]}'
    assert client.get(path, headers=a).status_code == 200
    for method in ("GET", "PATCH", "PUT", "DELETE"):
        response = client.open(path, method=method, headers=b, json=shift_data())
        assert response.status_code == 404
    assert client.get("/shifts", headers=b).json["data"] == []
    response = client.patch(path, headers=a, json={"location": "Back room"})
    assert response.status_code == 200 and response.json["location"] == "Back room"
    assert client.put(path, headers=a, json={"location": "Only one field"}).status_code == 400
    assert client.put(path, headers=a, json=shift_data()).status_code == 200
    assert client.delete(path, headers=a).status_code == 204
    assert client.get(path, headers=a).status_code == 404
    assert client.delete(path, headers=a).status_code == 404


@pytest.mark.parametrize("changes", [{"role_title": ""}, {"location": 7}, {"notes": []},
    {"start_time": "bad"}, {"start_time": "2026-12-01T08:00:00"},
    {"end_time": "2026-12-01T07:00:00-06:00"}, {"user_id": 99}])
def test_shift_validation(client, changes):
    headers = account(client)
    response = client.post("/shifts", headers=headers, json=shift_data(**changes))
    assert response.status_code == 400 and response.json["details"]


def test_failed_patch_does_not_save_partial_changes(client):
    headers = account(client)
    created = client.post("/shifts", headers=headers, json=shift_data())
    path = f'/shifts/{created.json["id"]}'
    response = client.patch(path, headers=headers, json={"location": "Changed", "end_time": "bad"})
    assert response.status_code == 400
    assert client.get(path, headers=headers).json["location"] == "Main store"
    assert client.patch(path, headers=headers, json={"start_time": "2027-01-01T00:00:00Z"}).status_code == 400


def test_pagination(client):
    headers = account(client)
    for _ in range(5):
        assert client.post("/shifts", headers=headers, json=shift_data()).status_code == 201
    for page, count in ((1, 2), (3, 1), (4, 0)):
        response = client.get(f"/shifts?page={page}&per_page=2", headers=headers)
        assert response.status_code == 200 and len(response.json["data"]) == count
        assert response.json["meta"] == {"page": page, "per_page": 2, "total": 5, "pages": 3}
    for query in ("page=0", "page=-1", "per_page=0", "per_page=51", "page=1.5", "per_page=abc"):
        assert client.get("/shifts?" + query, headers=headers).status_code == 400


def test_tokens_and_admin(app, client):
    headers = account(client)
    assert client.get("/admin/ping").status_code == 401
    assert client.get("/admin/ping", headers=headers).status_code == 403
    assert client.get("/auth/me", headers={"Authorization": "Bearer bad"}).status_code == 401
    now = datetime.now(timezone.utc)
    token = jwt.encode({"sub": "1", "iat": now - timedelta(minutes=2), "exp": now - timedelta(minutes=1)},
                        app.config["JWT_SECRET"], algorithm="HS256")
    expired = client.get("/auth/me", headers={"Authorization": "Bearer " + token})
    assert expired.status_code == 401 and expired.json["message"] == "Token expired"
    runner = app.test_cli_runner()
    result = runner.invoke(args=["create-admin", "--email", "admin@example.com"],
                           input="adminpassword123\nadminpassword123\n")
    assert result.exit_code == 0, result.output
    response = client.post("/auth/login", json={"email": "admin@example.com", "password": "adminpassword123"})
    admin_headers = {"Authorization": "Bearer " + response.json["access_token"]}
    assert client.get("/admin/ping", headers=admin_headers).status_code == 200


def test_relationship_and_foreign_key(app, client):
    headers = account(client)
    client.post("/shifts", headers=headers, json=shift_data())
    with app.app_context():
        user = db.session.scalar(db.select(User))
        assert user.shifts[0].user.id == user.id
        orphan = Shift(user_id=999, role_title="Test", location="Store",
                       start_time=datetime(2026, 12, 1, 8), end_time=datetime(2026, 12, 1, 16))
        db.session.add(orphan)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_health_and_framework_errors(client):
    assert client.get("/health").json == {"status": "ok"}
    for response, status in ((client.get("/missing"), 404), (client.post("/health"), 405),
                             (client.post("/auth/register", data="{", content_type="application/json"), 400)):
        assert response.status_code == status
        assert set(response.json) == {"error", "message", "details"}
