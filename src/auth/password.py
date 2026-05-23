import bcrypt

from src.auth.config import auth_settings


def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt(rounds=auth_settings.bcrypt_rounds)
    return bcrypt.hashpw(plain.encode(), salt).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def validate_password_strength(password: str) -> list[str]:
    errors = []
    if len(password) < auth_settings.min_password_length:
        errors.append(
            f"Senha deve ter no minimo {auth_settings.min_password_length} caracteres"
        )
    if not any(c.isupper() for c in password):
        errors.append("Senha deve conter ao menos uma letra maiuscula")
    if not any(c.islower() for c in password):
        errors.append("Senha deve conter ao menos uma letra minuscula")
    if not any(c.isdigit() for c in password):
        errors.append("Senha deve conter ao menos um digito")
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Senha deve conter ao menos um caractere especial")
    return errors
