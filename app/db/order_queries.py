# order_details.py
from app.db.catalog import get_connection
from mysql.connector import Error

def get_all_orders():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT z.id_заказы,
                   GROUP_CONCAT(t.название_товары SEPARATOR ', ') AS товары,
                   z.адрес_доставка,
                   z.время_доставка,
                   u.ФИО
            FROM Заказы z
            JOIN ТоварыВЗаказе tvz ON z.id_заказы = tvz.id_заказа
            JOIN Товары t ON tvz.id_товара = t.id_товары
            LEFT JOIN Пользователи u ON z.id_курьер = u.id_пользователя
            GROUP BY z.id_заказы, z.адрес_доставка, z.время_доставка, u.ФИО
            ORDER BY z.датат_заказ DESC
        """)
        orders = cursor.fetchall()
        return orders
    except Error as e:
        print(f"Ошибка при получении всех заказов: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_new_orders():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT z.id_заказы,
                   GROUP_CONCAT(t.название_товары SEPARATOR ', ') AS товары,
                   z.адрес_доставка,
                   z.время_доставка,
                   u.ФИО
            FROM Заказы z
            JOIN ТоварыВЗаказе tvz ON z.id_заказы = tvz.id_заказа
            JOIN Товары t ON tvz.id_товара = t.id_товары
            LEFT JOIN Пользователи u ON z.id_курьер = u.id_пользователя
            WHERE z.статус_заказ = 'новый'
            GROUP BY z.id_заказы, z.адрес_доставка, z.время_доставка, u.ФИО
            ORDER BY z.датат_заказ DESC
        """)
        orders = cursor.fetchall()
        return orders
    except Error as e:
        print(f"Ошибка при получении новых заказов: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_delivered_orders():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT z.id_заказы,
                   GROUP_CONCAT(t.название_товары SEPARATOR ', ') AS товары,
                   z.адрес_доставка,
                   z.время_доставка,
                   u.ФИО
            FROM Заказы z
            JOIN ТоварыВЗаказе tvz ON z.id_заказы = tvz.id_заказа
            JOIN Товары t ON tvz.id_товара = t.id_товары
            LEFT JOIN Пользователи u ON z.id_курьер = u.id_пользователя
            WHERE z.статус_заказ = 'доставлен'
            GROUP BY z.id_заказы, z.адрес_доставка, z.время_доставка, u.ФИО
            ORDER BY z.датат_заказ DESC
        """)
        orders = cursor.fetchall()
        return orders
    except Error as e:
        print(f"Ошибка при получении доставленных заказов: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_cancelled_orders():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT z.id_заказы,
                   GROUP_CONCAT(t.название_товары SEPARATOR ', ') AS товары,
                   z.адрес_доставка,
                   z.время_доставка,
                   u.ФИО
            FROM Заказы z
            JOIN ТоварыВЗаказе tvz ON z.id_заказы = tvz.id_заказа
            JOIN Товары t ON tvz.id_товара = t.id_товары
            LEFT JOIN Пользователи u ON z.id_курьер = u.id_пользователя
            WHERE z.статус_заказ = 'отклонен'
            GROUP BY z.id_заказы, z.адрес_доставка, z.время_доставка, u.ФИО
            ORDER BY z.датат_заказ DESC
        """)
        orders = cursor.fetchall()
        return orders
    except Error as e:
        print(f"Ошибка при получении отклоненных заказов: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_stores_from_order(order_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT DISTINCT m.название_магазин
            FROM ТоварыВЗаказе tvz
            JOIN Товары t ON tvz.id_товара = t.id_товары
            JOIN Магазин m ON t.id_магазин = m.id_магазин
            WHERE tvz.id_заказа = %s
        """, (order_id,))
        stores = cursor.fetchall()
        return ", ".join([store[0] for store in stores])
    except Error as e:
        print(f"Ошибка при получении магазинов из заказа: {e}")
        return ""
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()