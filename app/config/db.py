# Единые настройки подключения к MySQL
# .env ищется в корне проекта (не зависит от cwd / PyCharm)
import os
from pathlib import Path

from app.paths import PROJECT_ROOT

_ENV_FILE = PROJECT_ROOT / ".env"
_ENV_DOCKER = PROJECT_ROOT / ".env.docker"

try:
    from dotenv import load_dotenv

    # сначала docker-шаблон как fallback, потом .env перекрывает
    if _ENV_DOCKER.exists():
        load_dotenv(_ENV_DOCKER, override=False)
    if _ENV_FILE.exists():
        load_dotenv(_ENV_FILE, override=True)
except ImportError:
    pass


def _env(key: str, default: str) -> str:
    return os.getenv(key, default).strip()


# Дефолты = Docker Compose (см. .env.docker), чтобы работало даже без .env
DB_HOST = _env("MYSQL_HOST", "127.0.0.1")
DB_USER = _env("MYSQL_USER", "goget")
DB_PASSWORD = _env("MYSQL_PASSWORD", "goget")
DB_NAME = _env("MYSQL_DATABASE", "goget")
DB_PORT = int(_env("MYSQL_PORT", "3307"))


def connect_kwargs(include_database=True):
    cfg = {
        "host": DB_HOST,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "port": DB_PORT,
    }
    if include_database:
        cfg["database"] = DB_NAME
    return cfg
