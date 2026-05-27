from pathlib import Path

from fastapi.testclient import TestClient

from src.aerial_housing_detection.api.main import app

client = TestClient(app)


def test_web_auth_register_creates_user(tmp_path: Path) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "B626278",
            "email": "b626278@neoenergia.local",
            "full_name": "Lucas Soares",
            "password": "teste123",
        },
    )

    assert response.status_code in {200, 409}

    if response.status_code == 200:
        payload = response.json()

        assert payload["username"] == "B626278"
        assert payload["token_type"] == "bearer"
        assert payload["access_token"]
        assert payload["refresh_token"]


def test_web_auth_login_accepts_registered_user() -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "B626279",
            "email": "b626279@neoenergia.local",
            "full_name": "User Test",
            "password": "teste123",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "B626279",
            "password": "teste123",
        },
    )

    assert response.status_code == 200
    assert response.json()["username"] == "B626279"
    assert response.json()["access_token"]


def test_web_auth_login_rejects_invalid_password() -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "B626280",
            "email": "b626280@neoenergia.local",
            "full_name": "Invalid Password User",
            "password": "teste123",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "B626280",
            "password": "senhaerrada",
        },
    )

    assert response.status_code == 401


def test_web_auth_session_returns_authenticated_user() -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "B626281",
            "email": "b626281@neoenergia.local",
            "full_name": "Session User",
            "password": "teste123",
        },
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "B626281",
            "password": "teste123",
        },
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/session",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["authenticated"] is True
    assert response.json()["username"] == "B626281"


def test_web_auth_session_returns_false_without_token() -> None:
    response = client.get("/api/v1/auth/session")

    assert response.status_code == 200
    assert response.json()["authenticated"] is False
