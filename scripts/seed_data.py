"""Seed de dados para ambiente de desenvolvimento."""

import json
import sys
import urllib.request


BASE_URL = "http://localhost:8000"


def post(path: str, data: dict, token: str = "") -> dict:
    body = json.dumps(data).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"  ERRO {e.code} em {path}: {error_body}")
        return {}


def get(path: str, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    req = urllib.request.Request(f"{BASE_URL}{path}", headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"  ERRO {e.code} em {path}")
        return {}


def main() -> None:
    print("Verificando conexao...")
    try:
        req = urllib.request.Request(f"{BASE_URL}/health")
        with urllib.request.urlopen(req) as resp:
            health = json.loads(resp.read())
            print(f"  Status: {health.get('status')}")
    except Exception as e:
        print(f"Servidor indisponivel: {e}")
        sys.exit(1)

    print("\nLogin como admin...")
    login_resp = post("/api/v1/auth/login", {
        "email": "admin@aerial.local",
        "password": "admin123456",
    })
    admin_token = login_resp.get("access_token", "")
    if not admin_token:
        print("Falha no login admin. Verifique ADMIN_EMAIL e ADMIN_PASSWORD no .env")
        sys.exit(1)
    print("  OK")

    users = [
        {"email": "analista@paulista.pe.gov.br", "password": "analyst1234", "full_name": "Ana Costa", "role": "analyst"},
        {"email": "viewer@paulista.pe.gov.br", "password": "viewer12345", "full_name": "Carlos Lima", "role": "viewer"},
        {"email": "analista2@paulista.pe.gov.br", "password": "analyst1234", "full_name": "Beatriz Souza", "role": "analyst"},
    ]

    print("\nCriando usuarios...")
    for user in users:
        resp = post("/api/v1/auth/register", user, admin_token)
        if resp.get("id"):
            print(f"  {user['email']} ({user['role']})")
        else:
            print(f"  {user['email']} (ja existe ou erro)")

    print("\nCriando API keys...")
    api_keys = [
        {"name": "power-apps-dev", "expires_in_days": 30},
        {"name": "script-automatico", "expires_in_days": 90},
    ]
    for key_data in api_keys:
        resp = post("/api/v1/auth/api-keys", key_data, admin_token)
        if resp.get("key"):
            print(f"  {key_data['name']}: {resp['key'][:20]}...")
        else:
            print(f"  {key_data['name']}: erro")

    print("\nRegistrando consentimento de teste...")
    post("/api/v1/lgpd/consent", {
        "subject_id": "test-subject-001",
        "purpose": "social_policy",
        "legal_basis": "LGPD Art. 7, III",
    }, admin_token)
    print("  OK")

    print("\nVerificando metricas...")
    metrics = get("/api/v1/monitoring/metrics", admin_token)
    if metrics:
        print(f"  Total predictions: {metrics.get('total_predictions', 0)}")

    print("\nSeed concluido.")
    print("\nCredenciais de teste:")
    print(f"  Admin:    admin@aerial.local / admin123456")
    for user in users:
        print(f"  {user['role'].capitalize():10s} {user['email']} / {user['password']}")


if __name__ == "__main__":
    main()
