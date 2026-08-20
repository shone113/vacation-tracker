from app.core.security import hash_password, verify_password


def test_password_is_hashed_not_stored_as_plaintext():
    assert hash_password("Secret123!") != "Secret123!"


def test_correct_password_verifies():
    hashed = hash_password("Secret123!")
    assert verify_password("Secret123!", hashed) is True


def test_wrong_password_fails():
    hashed = hash_password("Secret123!")
    assert verify_password("WrongPassword", hashed) is False
