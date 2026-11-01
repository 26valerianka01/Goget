"""Каталог: категории, товары, вспомогательные запросы к магазинам."""
from mysql.connector import Error

from app.db.connection import get_connection

__all__ = [
    "get_connection",
    "get_categories",
    "get_user_data",
    "get_product_quantity",
    "get_products_by_category",
    "get_orders",
    "get_items_from_order",
    "get_store_id_from_item",
    "get_store_address",
]

def get_categories():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT название_категория FROM Категория")
        categories = cursor.fetchall()
        return [category[0] for category in categories]
    except Error as e:
        print(f"Ошибка при получении категорий: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_user_data(user_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT ФИО, пароль, эл_почта, номер_телефона, роль FROM Пользователи WHERE id_пользователя = %s", (user_id,))
        result = cursor.fetchone()
        return result if result else None
    except Error as e:
        print(f"Ошибка при получении данных пользователя: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_product_quantity(product_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT количество_товаров FROM Товары WHERE id_товары = %s", (product_id,))
        result = cursor.fetchone()
        return result[0] if result else 0
    except Error as e:
        print(f"Ошибка при получении количества товара: {e}")
        return 0
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_products_by_category(category):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT t.id_товары, t.название_товары, t.описание_товары, t.цена_товары,
                   t.путь_к_изображению, t.id_магазин, m.название_магазин
            FROM Товары t
            JOIN Магазин m ON t.id_магазин = m.id_магазин
            JOIN КатегорияТовары ct ON t.id_товары = ct.id_товары
            JOIN Категория c ON ct.id_категория = c.id_категория
            WHERE c.название_категория = %s
            """,
            (category,),
        )
        products = cursor.fetchall()
        # id, название, описание, цена, путь, id_магазин, название_магазина
        return [(p[0], p[1], p[2], str(p[3]), str(p[4]), p[5], p[6]) for p in products]
    except Error as e:
        print(f"Ошибка при получении продуктов: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_orders():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id_заказы, адрес_доставка FROM Заказы")
        return cursor.fetchall()
    except Error as e:
        print(f"Ошибка при получении заказов: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_items_from_order(order_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id_товара FROM ТоварыВЗаказе WHERE id_заказа = %s", (order_id,))
        return cursor.fetchall()
    except Error as e:
        print(f"Ошибка при получении товаров из заказа: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_store_id_from_item(item_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id_магазин FROM Товары WHERE id_товары = %s", (item_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Error as e:
        print(f"Ошибка при получении id_магазина из товара: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_store_address(store_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT адрес_магазин FROM Магазин WHERE id_магазин = %s", (store_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Error as e:
        print(f"Ошибка при получении адреса магазина: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()