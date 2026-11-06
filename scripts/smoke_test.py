"""Run a small end-to-end check against a local or live API."""
import json
import sys
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen

base = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000").rstrip("/")
suffix = uuid.uuid4().hex[:10]
password = "Test-password-123"


def call(method, path, expected, body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = json.dumps(body).encode() if body is not None else None
    request = Request(base + path, data=data, headers=headers, method=method)
    try:
        response = urlopen(request, timeout=60)
    except HTTPError as error:
        response = error
    with response:
        status = response.code
        text = response.read().decode()
    result = json.loads(text) if text else None
    safe = dict(result) if isinstance(result, dict) else result
    if isinstance(safe, dict) and "access_token" in safe:
        safe["access_token"] = "<hidden>"
    print(f"{method} {path} -> {status}")
    print(json.dumps(safe))
    assert status == expected, f"Expected {expected}, got {status}"
    return result


def make_account(letter):
    body = {"email": f"smoke-{letter}-{suffix}@example.com", "password": password}
    call("POST", "/auth/register", 201, body)
    token = call("POST", "/auth/login", 200, body)["access_token"]
    return body, token


call("GET", "/health", 200)
user_a, token_a = make_account("a")
user_b, token_b = make_account("b")
call("POST", "/auth/register", 409, user_a)
call("POST", "/auth/register", 400, {"email": "bad"})
wrong = call("POST", "/auth/login", 401, {"email": user_a["email"], "password": "wrong"})
unknown = call("POST", "/auth/login", 401, {"email": f"missing-{suffix}@example.com", "password": "wrong"})
assert wrong == unknown
call("GET", "/users/me", 401)
call("GET", "/users/me", 401, token="bad")
profile = call("GET", "/users/me", 200, token=token_a)
assert "password_hash" not in profile
call("PATCH", "/users/me", 200, {"full_name": "Test Manager", "role": "admin"}, token_a)
assert call("GET", "/users/me", 200, token=token_b)["full_name"] is None
call("GET", "/admin/ping", 401)
call("GET", "/admin/ping", 403, token=token_a)

body = {"role_title": "Floor lead", "location": "Main store",
        "start_time": "2026-12-01T08:00:00-06:00", "end_time": "2026-12-01T16:00:00-06:00",
        "notes": "Smoke test"}
shift = call("POST", "/shifts", 201, body, token_a)
path = f'/shifts/{shift["id"]}'
call("GET", path, 200, token=token_a)
for method in ("GET", "PATCH", "PUT", "DELETE"):
    call(method, path, 404, body if method in ("PATCH", "PUT") else None, token_b)
assert call("GET", "/shifts", 200, token=token_b)["data"] == []
call("PATCH", path, 400, {"end_time": "bad"}, token_a)
call("PATCH", path, 200, {"location": "Back room"}, token_a)
assert call("GET", path, 200, token=token_a)["location"] == "Back room"
call("PUT", path, 200, body, token_a)
ids = [shift["id"]]
for _ in range(4):
    ids.append(call("POST", "/shifts", 201, body, token_a)["id"])
for page, count in ((1, 2), (3, 1), (4, 0)):
    result = call("GET", f"/shifts?page={page}&per_page=2", 200, token=token_a)
    assert len(result["data"]) == count and result["meta"]["total"] == 5
call("GET", "/shifts?per_page=51", 400, token=token_a)
for shift_id in ids:
    call("DELETE", f"/shifts/{shift_id}", 204, token=token_a)
call("GET", path, 404, token=token_a)
call("DELETE", path, 404, token=token_a)
print("PASS: health, auth, profiles, CRUD, ownership, errors, and pagination.")
