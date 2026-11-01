import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.auth.passwords import hash_password, needs_rehash, verify_password


def test_hash_and_verify():
    h = hash_password("secret123")
    assert h.startswith("$2b$")
    assert verify_password("secret123", h)
    assert not verify_password("wrong", h)


def test_legacy_plaintext_compat():
    assert verify_password("4", "4")
    assert needs_rehash("4")
    assert not needs_rehash(hash_password("4"))
