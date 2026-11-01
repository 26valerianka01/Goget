"""
Демо-заказы для курьера (2 маршрута на карте).
Запуск: python scripts/seed_courier_demo.py
"""
import sys
from pathlib import Path

import mysql.connector

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config.db import connect_kwargs


def main():
    conn = mysql.connector.connect(**connect_kwargs(True))
    cur = conn.cursor()

    # Курьер №1 - Иванов (user1@example.com / password1)
    courier_id = 1
    # Демо-клиент
    cur.execute("SELECT id_пользователя FROM Пользователи WHERE эл_почта='client@example.com'")
    client = cur.fetchone()
    client_id = client[0] if client else 11

    # Товары: Melasti (магазин 1), диван Hoff (магазин 3) - разные заказы
    cur.execute("SELECT id_товары, цена_товары, id_магазин FROM Товары WHERE название_товары LIKE 'Melasti%' LIMIT 1")
    p1 = cur.fetchone()
    cur.execute("SELECT id_товары, цена_товары, id_магазин FROM Товары WHERE название_товары LIKE 'Диван-кровать%' LIMIT 1")
    p2 = cur.fetchone()
    if not p1 or not p2:
        cur.execute("SELECT id_товары, цена_товары, id_магазин FROM Товары ORDER BY id_товары LIMIT 2")
        rows = cur.fetchall()
        p1, p2 = rows[0], rows[1]

    cur.execute("SELECT адрес_магазин FROM Магазин WHERE id_магазин=%s", (p1[2],))
    store1_addr = cur.fetchone()[0]
    cur.execute("SELECT адрес_магазин FROM Магазин WHERE id_магазин=%s", (p2[2],))
    store2_addr = cur.fetchone()[0]

    # Удаляем старые демо-заказы 201/202 если были
    for oid in (201, 202):
        cur.execute("DELETE FROM ТочкиМаршрута WHERE id_заказы=%s", (oid,))
        cur.execute("DELETE FROM ТоварыВЗаказе WHERE id_заказа=%s", (oid,))
        cur.execute("DELETE FROM ИсторияЗаказов WHERE id_заказы=%s", (oid,))
        cur.execute("DELETE FROM Заказы WHERE id_заказы=%s", (oid,))

    # Заказ 201 - косметика, Золотое яблоко → Ленина
    cur.execute(
        """
        INSERT INTO Заказы (id_заказы, id_пользователя, id_магазин, статус_заказ, датат_заказ,
            адрес_доставка, время_доставка, стоимость_заказ, id_курьер, действие_модератор)
        VALUES (201, %s, %s, 'в_процессе', NOW(),
            'проспект Ленина, 50, Екатеринбург', DATE_ADD(NOW(), INTERVAL 1 DAY), %s, %s, 'утвердить')
        """,
        (client_id, p1[2], float(p1[1]), courier_id),
    )
    cur.execute(
        "INSERT INTO ТоварыВЗаказе (id_заказа, id_товара, количество) VALUES (201, %s, 1)",
        (p1[0],),
    )

    # Заказ 202 - мебель, Hoff → Малышева
    cur.execute(
        """
        INSERT INTO Заказы (id_заказы, id_пользователя, id_магазин, статус_заказ, датат_заказ,
            адрес_доставка, время_доставка, стоимость_заказ, id_курьер, действие_модератор)
        VALUES (202, %s, %s, 'в_процессе', NOW(),
            'улица Малышева, 36, Екатеринбург', DATE_ADD(NOW(), INTERVAL 2 DAY), %s, %s, 'утвердить')
        """,
        (client_id, p2[2], float(p2[1]), courier_id),
    )
    cur.execute(
        "INSERT INTO ТоварыВЗаказе (id_заказа, id_товара, количество) VALUES (202, %s, 1)",
        (p2[0],),
    )

    # Маршруты курьера (по одному на заказ - так на карте видно два пути)
    cur.execute(
        """
        INSERT INTO Маршрут (id_курьер, начальная_точка, конечная_точка, расстояние_маршрут, длительность_маршрут)
        VALUES (%s, %s, 'проспект Ленина, 50, Екатеринбург', 3.50, 20)
        """,
        (courier_id, store1_addr),
    )
    r1 = cur.lastrowid
    cur.execute(
        """
        INSERT INTO ТочкиМаршрута (id_маршрут, координаты_ТочкиМаршрута, тип_ТочкиМаршрута, id_заказы)
        VALUES (%s, %s, 'забрать', 201), (%s, 'проспект Ленина, 50, Екатеринбург', 'доставить', 201)
        """,
        (r1, store1_addr, r1),
    )

    cur.execute(
        """
        INSERT INTO Маршрут (id_курьер, начальная_точка, конечная_точка, расстояние_маршрут, длительность_маршрут)
        VALUES (%s, %s, 'улица Малышева, 36, Екатеринбург', 4.10, 25)
        """,
        (courier_id, store2_addr),
    )
    r2 = cur.lastrowid
    cur.execute(
        """
        INSERT INTO ТочкиМаршрута (id_маршрут, координаты_ТочкиМаршрута, тип_ТочкиМаршрута, id_заказы)
        VALUES (%s, %s, 'забрать', 202), (%s, 'улица Малышева, 36, Екатеринбург', 'доставить', 202)
        """,
        (r2, store2_addr, r2),
    )

    cur.execute("UPDATE Курьер SET текущие_заказы = 2, статус_курьер='доступен' WHERE id_курьер=%s", (courier_id,))

    # Заказ 139 из seed - тоже на этого курьера
    cur.execute("UPDATE Заказы SET id_курьер=%s, статус_заказ='в_процессе' WHERE id_заказы=139", (courier_id,))
    cur.execute("SELECT DISTINCT id_маршрут FROM ТочкиМаршрута WHERE id_заказы=139 AND id_маршрут IS NOT NULL")
    for (rid,) in cur.fetchall():
        cur.execute("UPDATE Маршрут SET id_курьер=%s WHERE id_маршрут=%s", (courier_id, rid))

    conn.commit()
    cur.execute("SELECT id_заказы, статус_заказ, адрес_доставка FROM Заказы WHERE id_курьер=%s", (courier_id,))
    orders = cur.fetchall()
    cur.execute("SELECT id_маршрут, начальная_точка, конечная_точка FROM Маршрут WHERE id_курьер=%s", (courier_id,))
    routes = cur.fetchall()
    print("Готово. Заказы курьера:", orders)
    print("Маршруты:", routes)
    print()
    print("Модератор: user4@example.com / 4")
    print("Курьер:    user1@example.com / password1")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
