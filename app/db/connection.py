"""Подключение к MySQL."""
from __future__ import annotations

import mysql.connector

from app.config.db import connect_kwargs


def get_connection():
    return mysql.connector.connect(**connect_kwargs(True))
