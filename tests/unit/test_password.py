from src.auth.password import hash_password, validate_password_strength, verify_password


class TestHashPassword:
    def test_hashes_password(self):
        hashed = hash_password("Test@1234")
        assert hashed != "Test@1234"
        assert hashed.startswith("$2b$")

    def test_different_hashes_for_same_input(self):
        h1 = hash_password("Test@1234")
        h2 = hash_password("Test@1234")
        assert h1 != h2


class TestVerifyPassword:
    def test_correct_password(self):
        hashed = hash_password("Test@1234")
        assert verify_password("Test@1234", hashed) is True

    def test_wrong_password(self):
        hashed = hash_password("Test@1234")
        assert verify_password("Wrong@1234", hashed) is False


class TestValidatePasswordStrength:
    def test_valid_password(self):
        errors = validate_password_strength("Test@1234")
        assert errors == []

    def test_short_password(self):
        errors = validate_password_strength("T@1")
        assert any("minimo" in e for e in errors)

    def test_no_uppercase(self):
        errors = validate_password_strength("test@1234")
        assert any("maiuscula" in e for e in errors)

    def test_no_lowercase(self):
        errors = validate_password_strength("TEST@1234")
        assert any("minuscula" in e for e in errors)

    def test_no_digit(self):
        errors = validate_password_strength("Test@abcd")
        assert any("digito" in e for e in errors)

    def test_no_special(self):
        errors = validate_password_strength("Test12345")
        assert any("especial" in e for e in errors)
