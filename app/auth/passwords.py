"""Хеширование и проверка паролей (bcrypt)."""
from __future__ import annotations

import bcrypt


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, stored: str) -> bool:
    """Проверяет bcrypt-хеш. Для старых plaintext-записей - одноразовое сравнение."""
    if not plain or not stored:
        return False
    if stored.startswith("$2a$") or stored.startswith("$2b$") or stored.startswith("$2y$"):
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), stored.encode("utf-8"))
        except (ValueError, TypeError):
            return False
    # legacy plaintext (до миграции) - только для совместимости со старой БД
    return plain == stored


def needs_rehash(stored: str) -> bool:
    return not (
        stored.startswith("$2a$") or stored.startswith("$2b$") or stored.startswith("$2y$")
    )
