"""Seed de dados para ambiente de desenvolvimento."""

import json
import sys
import urllib.error
import urllib.request
from typing import Any

BASE_URL = "http://localhost:8000"


def post(path: str, data: dict[str, Any], token: str = "") -> dict[str, Any]:
    body = json.dumps(data).encode()
    headers = {"Content-Type": "application/json"}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        error_body = error.read().decode()
        print(f"ERRO {error.code} em {path}: {error_body}")
        return {}


def get(path: str, token: str) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"}

    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers=headers,
    )

    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        print(f"ERRO {error.code} em {path}")
        return {}


def check_server_health() -> None:
    print("Verificando conexao...")

    try:
        request = urllib.request.Request(f"{BASE_URL}/health")

        with urllib.request.urlopen(request) as response:
            health = json.loads(response.read())
            print(f"Status: {health.get('status')}")
    except Exception as error:
        print(f"Servidor indisponivel: {error}")
        sys.exit(1)


def login_admin() -> str:
    print("\nLogin como admin...")

    login_response = post(
        "/api/v1/auth/login",
        {
            "email": "admin@aerial.local",
            "password": "admin123456",
        },
    )

    admin_token = login_response.get("access_token", "")

    if not admin_token:
        print("Falha no login admin. Verifique ADMIN_EMAIL e ADMIN_PASSWORD no .env")
        sys.exit(1)

    print("OK")
    return admin_token


def seed_users(admin_token: str) -> list[dict[str, str]]:
    users = [
        {
            "email": "analista@paulista.pe.gov.br",
            "password": "analyst1234",
            "full_name": "Ana Costa",
            "role": "analyst",
        },
        {
            "email": "viewer@paulista.pe.gov.br",
            "password": "viewer12345",
            "full_name": "Carlos Lima",
            "role": "viewer",
        },
        {
            "email": "analista2@paulista.pe.gov.br",
            "password": "analyst1234",
            "full_name": "Beatriz Souza",
            "role": "analyst",
        },
    ]

    print("\nCriando usuarios...")

    for user in users:
        response = post("/api/v1/auth/register", user, admin_token)

        if response.get("id"):
            print(f"{user['email']} ({user['role']})")
        else:
            print(f"{user['email']} (ja existe ou erro)")

    return users


def seed_api_keys(admin_token: str) -> None:
    api_keys = [
        {"name": "power-apps-dev", "expires_in_days": 30},
        {"name": "script-automatico", "expires_in_days": 90},
    ]

    print("\nCriando API keys...")

    for key_data in api_keys:
        response = post("/api/v1/auth/api-keys", key_data, admin_token)

        if response.get("key"):
            print(f"{key_data['name']}: {response['key'][:20]}...")
        else:
            print(f"{key_data['name']}: erro")


def seed_lgpd_consent(admin_token: str) -> None:
    print("\nRegistrando consentimento de teste...")

    post(
        "/api/v1/lgpd/consent",
        {
            "subject_id": "test-subject-001",
            "purpose": "social_policy",
            "legal_basis": "LGPD Art. 7, III",
        },
        admin_token,
    )

    print("OK")


def print_metrics(admin_token: str) -> None:
    print("\nVerificando metricas...")

    metrics = get("/api/v1/monitoring/metrics", admin_token)

    if metrics:
        print(f"Total predictions: {metrics.get('total_predictions', 0)}")


def print_credentials(users: list[dict[str, str]]) -> None:
    print("\nSeed concluido.")
    print("\nCredenciais de teste:")
    print("Admin:    admin@aerial.local / admin123456")

    for user in users:
        role = user["role"].capitalize()
        print(f"{role:10s} {user['email']} / {user['password']}")


def main() -> None:
    check_server_health()
    admin_token = login_admin()
    users = seed_users(admin_token)
    seed_api_keys(admin_token)
    seed_lgpd_consent(admin_token)
    print_metrics(admin_token)
    print_credentials(users)


if __name__ == "__main__":
    main()