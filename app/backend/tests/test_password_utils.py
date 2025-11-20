from app.backend.core import password_utils
from argon2 import PasswordHasher
import bcrypt

def test_verify_argon2():
    ph = PasswordHasher()
    h = ph.hash("secret123")
    assert password_utils.verify_hash("secret123", h) is True
    assert password_utils.verify_hash("wrong", h) is False

def test_verify_bcrypt():
    h = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode()
    assert password_utils.verify_hash("secret123", h) is True
    assert password_utils.verify_hash("wrong", h) is False

def test_verify_plain():
    assert password_utils.verify_hash("plain", "plain") is True
    assert password_utils.verify_hash("plain", "other") is False


def test_verify_argon2_and_bcrypt_exceptions(monkeypatch):
    # force argon2 verify to raise -> verify_hash should return False for argon2 branch
    # replace the password_hasher with a stub that raises on verify
    class StubPH:
        def verify(self, stored, user_input):
            raise Exception("argon error")

    monkeypatch.setattr(password_utils, 'password_hasher', StubPH())
    assert password_utils.verify_hash('any', '$argon2bad') is False

    # force bcrypt.checkpw to raise -> verify_hash should return False for bcrypt branch
    def fake_bcrypt(a, b):
        raise Exception('bcrypt error')

    monkeypatch.setattr(bcrypt, 'checkpw', fake_bcrypt)
    assert password_utils.verify_hash('any', '$2b$invalid') is False