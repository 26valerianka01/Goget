"""
Построение маршрута заказа.

Алгоритм (с учётом доставки):
1) Точки «забрать» (магазины) + точка «доставить» (клиент).
2) Порядок заборов: Nearest Neighbor + улучшение 2-opt (Haversine).
3) Доставка всегда в конце (бизнес-ограничение).
4) В Маршрут пишем расстояние (км) и оценку времени (мин).
"""
from app.db.catalog import get_connection, get_store_id_from_item, get_store_address
from mysql.connector import Error
from app.services.geocode import distance_between_points


def insert_route(id_курьер, начальная_точка, конечная_точка, расстояние_маршрут, длительность_маршрут):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO Маршрут (id_курьер, начальная_точка, конечная_точка, расстояние_маршрут, длительность_маршрут)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (id_курьер, начальная_точка, конечная_точка, расстояние_маршрут, длительность_маршрут),
        )
        connection.commit()
        return cursor.lastrowid
    except Error as e:
        print(f"Ошибка при вставке маршрута: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def insert_route_point(id_маршрут, координаты_ТочкиМаршрута, тип_ТочкиМаршрута, id_заказы):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO ТочкиМаршрута (id_маршрут, координаты_ТочкиМаршрута, тип_ТочкиМаршрута, id_заказы)
            VALUES (%s, %s, %s, %s)
            """,
            (id_маршрут, координаты_ТочкиМаршрута, тип_ТочкиМаршрута, id_заказы),
        )
        connection.commit()
    except Error as e:
        print(f"Ошибка при вставке точки маршрута: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_distance(coord1, coord2):
    return distance_between_points(coord1, coord2)


def _path_length(points):
    total = 0.0
    for i in range(len(points) - 1):
        d = get_distance(points[i], points[i + 1])
        if d >= 1e8:
            return 1e9
        total += d
    return total


def nearest_neighbor_order(points, start_idx=0):
    """Жадный NN: порядок индексов, начиная со start_idx."""
    if not points:
        return []
    remaining = set(range(len(points)))
    order = [start_idx]
    remaining.remove(start_idx)
    while remaining:
        last = order[-1]
        nxt = min(remaining, key=lambda i: get_distance(points[last], points[i]))
        order.append(nxt)
        remaining.remove(nxt)
    return order


def two_opt(points, order):
    """Локальное улучшение 2-opt для порядка индексов."""
    if len(order) < 4:
        return order
    best = order[:]
    improved = True
    while improved:
        improved = False
        for i in range(1, len(best) - 2):
            for j in range(i + 1, len(best)):
                if j - i == 1:
                    continue
                new_order = best[:i] + best[i:j][::-1] + best[j:]
                if _path_length([points[k] for k in new_order]) + 1e-9 < _path_length(
                    [points[k] for k in best]
                ):
                    best = new_order
                    improved = True
        # один проход достаточно часто; цикл while ловит цепочку улучшений
    return best


def optimize_pickups(pickup_addrs):
    """Оптимальный обход магазинов: NN от каждой стартовой + 2-opt, лучший путь."""
    unique = list(dict.fromkeys(pickup_addrs))
    if len(unique) <= 1:
        return unique

    best_path = None
    best_len = 1e18
    for start in range(len(unique)):
        order = nearest_neighbor_order(unique, start)
        order = two_opt(unique, order)
        path = [unique[i] for i in order]
        length = _path_length(path)
        if length < best_len:
            best_len = length
            best_path = path
    return best_path or unique


def create_route_with_points(order_id, delivery_address):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id_товара FROM ТоварыВЗаказе WHERE id_заказа = %s", (order_id,))
        items = cursor.fetchall()
        store_addresses = []
        for (item_id,) in items:
            store_id = get_store_id_from_item(item_id)
            if store_id:
                store_address = get_store_address(store_id)
                if store_address:
                    store_addresses.append(store_address)

        # очистим старые точки заказа (если пересоздаём)
        cursor.execute("DELETE FROM ТочкиМаршрута WHERE id_заказы = %s", (order_id,))
        connection.commit()

        pickups = optimize_pickups(store_addresses)
        # Доставка всегда последняя
        ordered_addrs = pickups + [delivery_address]
        types = ["забрать"] * len(pickups) + ["доставить"]

        for addr, ptype in zip(ordered_addrs, types):
            insert_route_point(None, addr, ptype, order_id)

        if not ordered_addrs:
            print("Нет точек маршрута для данного заказа.")
            return

        dist = _path_length(ordered_addrs)
        if dist >= 1e8:
            dist = 0.0
        # ~25 км/ч в городе + 10 мин на каждую остановку
        duration = int(dist / 25 * 60) + 10 * len(ordered_addrs)

        route_id = insert_route(None, ordered_addrs[0], delivery_address, round(dist, 2), duration)
        cursor.execute(
            "UPDATE ТочкиМаршрута SET id_маршрут = %s WHERE id_заказы = %s",
            (route_id, order_id),
        )
        connection.commit()
        return route_id
    except Error as e:
        print(f"Ошибка при создании маршрута: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
