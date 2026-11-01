import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db.catalog import (
    get_connection,
    get_categories,
    get_products_by_category,
)
from app.ui.order_window import get_couriers
from app.auth.users import UserManager
from app.config.db import DB_NAME


REQUIRED_TABLES = {
    "пользователи",
    "магазин",
    "категория",
    "товары",
    "категориятовары",
    "курьер",
    "заказы",
    "товарывзаказе",
    "маршрут",
    "точкимаршрута",
    "историязаказов",
}


@pytest.fixture
def connection():
    conn = get_connection()
    yield conn
    if conn.is_connected():
        conn.close()


@pytest.fixture
def user_manager():
    # сброс singleton между тестами
    UserManager._instance = None
    UserManager.current_user_id = None
    um = UserManager()
    yield um
    UserManager._instance = None
    UserManager.current_user_id = None


def test_mysql_connection(connection):
    cur = connection.cursor()
    cur.execute("SELECT DATABASE()")
    assert cur.fetchone()[0].lower() == DB_NAME.lower()
    cur.close()


def test_required_tables_exist(connection):
    cur = connection.cursor()
    cur.execute("SHOW TABLES")
    tables = {row[0].lower() for row in cur.fetchall()}
    missing = REQUIRED_TABLES - tables
    assert not missing, f"Нет таблиц: {missing}"
    cur.close()


def test_seed_has_categories():
    cats = get_categories()
    assert isinstance(cats, list)
    assert len(cats) >= 1
    assert "Косметика" in cats


def test_products_in_cosmetics():
    products = get_products_by_category("Косметика")
    assert len(products) >= 1
    # id, название, описание, цена, путь, id_магазин, название_магазина
    assert len(products[0]) >= 6
    assert products[0][6]  # магазин указан


def test_couriers_available():
    couriers = get_couriers()
    assert len(couriers) >= 1
    assert all(len(c) == 2 for c in couriers)


@patch("app.auth.users.messagebox")
def test_login_moderator(mock_mb, user_manager):
    role = user_manager.login_user("user4@example.com", "4")
    assert role == "модератор"
    assert user_manager.get_current_user_id() is not None


@patch("app.auth.users.messagebox")
def test_login_courier(mock_mb, user_manager):
    role = user_manager.login_user("user1@example.com", "password1")
    assert role == "курьер"


@patch("app.auth.users.messagebox")
def test_login_wrong_password(mock_mb, user_manager):
    role = user_manager.login_user("user4@example.com", "wrong")
    assert role is None


def test_stores_and_users_counts(connection):
    cur = connection.cursor()
    cur.execute("SELECT COUNT(*) FROM Магазин")
    assert cur.fetchone()[0] >= 10
    cur.execute("SELECT COUNT(*) FROM Пользователи")
    assert cur.fetchone()[0] >= 5
    cur.execute("SELECT COUNT(*) FROM Товары")
    assert cur.fetchone()[0] >= 10
    cur.close()


def test_order_items_schema(connection):
    cur = connection.cursor()
    cur.execute("DESCRIBE ТоварыВЗаказе")
    cols = {row[0] for row in cur.fetchall()}
    assert "id_заказа" in cols
    assert "id_товара" in cols
    cur.execute("DESCRIBE ТочкиМаршрута")
    cols = {row[0] for row in cur.fetchall()}
    assert "id_заказы" in cols
    cur.close()
