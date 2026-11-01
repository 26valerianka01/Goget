import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ui.auth_windows import validate_username, validate_phone, validate_email
from app.ui.user_window import validate_fio


def test_validate_phone_ok():
    assert validate_phone("+79991234567")


def test_validate_phone_bad():
    assert not validate_phone("89991234567")
    assert not validate_phone("+799912345")
    assert not validate_phone("")


def test_validate_email_ok():
    assert validate_email("user4@example.com")
    assert validate_email("client@example.com")


def test_validate_email_bad():
    assert not validate_email("not-an-email")
    assert not validate_email("a@b")
    assert not validate_email("")


def test_validate_username_cyrillic_fio():
    assert validate_username("Иванов Иван Иванович")
    assert validate_username("Анна")


def test_validate_username_rejects_empty_and_digits_only_mixed_invalid():
    assert not validate_username("")
    assert not validate_username("user@mail")


def test_validate_fio():
    assert validate_fio("Сидоров Сидор Сидорович")
    assert not validate_fio("John123")
