"""Настройка логирования приложения."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.paths import LOGS_DIR


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("goget")
    if logger.handlers:
        return logger

    logger.setLevel(level)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        LOGS_DIR / "app.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    console.setFormatter(fmt)
    logger.addHandler(console)

    return logger
