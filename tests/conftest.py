import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.auth.models import Role
from src.auth.password import hash_password
from src.auth.store import user_store
from src.auth.tokens import create_access_token


@pytest.fixture(autouse=True)
def _clean_stores():
    user_store.clear()
    yield
    user_store.clear()


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def client(app):
    return TestClient(app)


@pytest.fixture()
def seed_users():
    users = {}
    for username, role in [
        ("admin", Role.ADMIN),
        ("analyst", Role.ANALYST),
        ("viewer", Role.VIEWER),
    ]:
        user = user_store.create(
            username=username,
            email=f"{username}@test.com",
            full_name=f"Test {username.title()}",
            hashed_password=hash_password("Test@1234"),
            role=role,
        )
        users[username] = user
    return users


@pytest.fixture()
def admin_headers(seed_users):
    token = create_access_token("admin", Role.ADMIN.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def analyst_headers(seed_users):
    token = create_access_token("analyst", Role.ANALYST.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def viewer_headers(seed_users):
    token = create_access_token("viewer", Role.VIEWER.value)
    return {"Authorization": f"Bearer {token}"}
