"""Пути проекта - не зависят от cwd."""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = PROJECT_ROOT / "assets"
LOGS_DIR = PROJECT_ROOT / "logs"


def asset(*parts: str | Path) -> str:
    """Абсолютный путь к файлу в assets/ (строка для Image.open / БД-совместимости)."""
    return str(ASSETS_DIR.joinpath(*parts))
