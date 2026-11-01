import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db.catalog import get_connection
from app.services.routing import create_route_with_points, insert_route_point
from app.auth.users import UserManager


@pytest.fixture
def clean_user_manager():
    UserManager._instance = None
    UserManager.current_user_id = None
    um = UserManager()
    yield um
    UserManager._instance = None
    UserManager.current_user_id = None


def _fetch_one(sql, params=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def test_create_route_points_for_existing_order():
    """Проверяем, что для заказа создаются точки маршрута без падения на id_заказы."""
    row = _fetch_one(
        "SELECT id_заказы, адрес_доставка FROM Заказы ORDER BY id_заказы DESC LIMIT 1"
    )
    if not row:
        pytest.skip("Нет заказов в БД - сначала оформите заказ в приложении")
    order_id, address = row

    # удалим старые тестовые точки без маршрута, чтобы не копить дубликаты
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM ТочкиМаршрута WHERE id_заказы = %s AND id_маршрут IS NULL",
        (order_id,),
    )
    conn.commit()
    cur.close()
    conn.close()

    # вставка одной точки напрямую
    insert_route_point(None, address or "ул. Ленина 3, Екатеринбург", "доставить", order_id)
    row = _fetch_one(
        "SELECT COUNT(*) FROM ТочкиМаршрута WHERE id_заказы = %s",
        (order_id,),
    )
    assert row[0] >= 1


@patch("app.auth.users.messagebox")
def test_moderator_can_see_orders(mock_mb, clean_user_manager):
    role = clean_user_manager.login_user("user4@example.com", "4")
    assert role == "модератор"
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Заказы")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    assert count >= 0
