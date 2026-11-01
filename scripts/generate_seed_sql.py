"""Генерирует docker/mysql/init/02_seed.sql из тех же данных, что fill_db.py."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.auth.passwords import hash_password

OUT = ROOT / "docker" / "mysql" / "init" / "02_seed.sql"


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "''")


def img(n: int) -> str:
    # относительный путь от корня проекта (кроссплатформенно для Pillow)
    return f"assets/Для базы/{n}.png"


def main() -> None:
    users_plain = [
        ("Иванов Иван Иванович", "password1", "user1@example.com", "+79991234567", "курьер"),
        ("Петров Петр Петрович", "password2", "user2@example.com", "+79991234568", "курьер"),
        ("Сидоров Сидор Сидорович", "password3", "user3@example.com", "+79991234569", "клиент"),
        ("Кузнецов Кузьма Кузьмич", "4", "user4@example.com", "+79991234570", "модератор"),
        ("Смирнов Сергей Сергеевич", "password5", "user5@example.com", "+79991234571", "курьер"),
        ("Попов Павел Павлович", "password6", "user6@example.com", "+79991234572", "клиент"),
        ("Васильев Василий Васильевич", "7", "user7@example.com", "+79999999999", "курьер"),
        ("Соколов Сергей Соколович", "password8", "user8@example.com", "+79991234574", "клиент"),
        ("Михайлов Михаил Михайлович", "password9", "user9@example.com", "+79991234575", "клиент"),
        ("Зайцев Захар Захарович", "password10", "user10@example.com", "+79991234576", "курьер"),
        ("Алексеева Анна", "6", "client@example.com", "+79991234580", "клиент"),
        ("Морозова Елена", "0", "client3@example.com", "+79991234582", "клиент"),
        ("Федорова Мария", "1234567", "client2@example.com", "+79991234581", "клиент"),
    ]
    users = [(fio, hash_password(pw), email, phone, role) for fio, pw, email, phone, role in users_plain]
    stores = [
        ("Золотое яблоко", "ул. Малышева, 71, Екатеринбург", "+78007707021", "mediaoffice@goldapple.ru"),
        ("РИВ ГОШ", "ул. 8 Марта, 46, Екатеринбург", "+78002344460", "shopadmin@rivegauche.ru"),
        ("Hoff", "ул. Репина, 94, Екатеринбург", "+73433023593", "info@hoff.ru"),
        ("Много Мебели", "ул. Блюхера, 39, Екатеринбург", "+79221295115", "zakaz@mnogomebeli.com"),
        ("Toy.ru", "ул. 8 Марта, 46, Екатеринбург", "+78007003470", "info@toy.ru"),
        ("Детский мир", "ул. 8 Марта, 46, Екатеринбург", "+78002500000", "ur@detmir.ru"),
        ("Lime", "ул. 8 Марта, 46, Екатеринбург", "+73433111609", "shop@lime.com"),
        ("Love Republic", "ул. Вайнера, 9, Екатеринбург", "+78003007755", "info@loverepublic.ru"),
        ("DNS", "просп. Ленина, 48, Екатеринбург", "+78007707999", "opt_ekb@dns-shop.ru"),
        ("RBT.ru", "ул. Луначарского, 205, Екатеринбург", "+73433820644", "rasotd@rbt.ru"),
    ]
    categories = ["Косметика", "Мебель", "Детские товары", "Одежда", "Электроника", "Игрушки"]

    # читаем products из scripts/fill_db.py, чтобы не дублировать вручную
    fill = (ROOT / "scripts" / "fill_db.py").read_text(encoding="utf-8")
    block = re.search(r"products = \[(.*?)\n    \]", fill, re.S)
    if not block:
        raise SystemExit("Не найден список products в scripts/fill_db.py")
    products = eval("[" + block.group(1) + "]", {"__builtins__": {}})

    lines: list[str] = [
        "-- GoGet demo seed (applied on first container start)",
        "SET NAMES utf8mb4;",
        "SET FOREIGN_KEY_CHECKS = 0;",
        "",
        "INSERT INTO Пользователи (ФИО, пароль, эл_почта, номер_телефона, роль) VALUES",
    ]
    lines.append(
        ",\n".join(
            f"('{esc(a)}', '{esc(b)}', '{esc(c)}', '{esc(d)}', '{esc(e)}')" for a, b, c, d, e in users
        )
        + ";"
    )
    lines += [
        "",
        "INSERT INTO Курьер (id_курьер, статус_курьер, текущие_заказы, трансстредство_курьер) VALUES",
        "(1,'доступен',0,'автомобиль'), (2,'доступен',0,'автомобиль'), (5,'доступен',0,'автомобиль'),",
        "(7,'доступен',0,'автомобиль'), (10,'доступен',0,'автомобиль');",
        "",
        "INSERT INTO Магазин (название_магазин, адрес_магазин, номер_тел_магазин, эл_почта_магазин) VALUES",
    ]
    lines.append(
        ",\n".join(f"('{esc(a)}', '{esc(b)}', '{esc(c)}', '{esc(d)}')" for a, b, c, d in stores) + ";"
    )
    lines += [
        "",
        "INSERT INTO Категория (название_категория) VALUES",
        ",\n".join(f"('{esc(c)}')" for c in categories) + ";",
        "",
        "INSERT INTO Товары (название_товары, описание_товары, цена_товары, id_магазин, id_категория, количество_товаров, путь_к_изображению) VALUES",
    ]
    prod_rows = []
    for name, desc, price, store_id, cat_id, qty, pic in products:
        prod_rows.append(
            f"('{esc(name)}', '{esc(desc)}', {float(price):.2f}, {store_id}, {cat_id}, {qty}, '{esc(img(pic))}')"
        )
    lines.append(",\n".join(prod_rows) + ";")

    # КатегорияТовары: id товаров 1..N в порядке вставки
    cat_links = []
    for i, (_, _, _, _, cat_id, _, _) in enumerate(products, start=1):
        cat_links.append(f"({cat_id}, {i})")
    lines += [
        "",
        "INSERT INTO КатегорияТовары (id_категория, id_товары) VALUES",
        ",\n".join(cat_links) + ";",
    ]

    # заказ 139: Melasti=2, PFC=3 при текущем порядке products (индексы 2 и 3)
    melasti_i = next(i for i, p in enumerate(products, 1) if str(p[0]).startswith("Melasti"))
    pfc_i = next(i for i, p in enumerate(products, 1) if str(p[0]).startswith("PFC"))
    # client@example.com = 11-й пользователь
    lines += [
        "",
        "INSERT INTO Заказы (id_заказы, id_пользователя, id_магазин, статус_заказ, датат_заказ, "
        "адрес_доставка, время_доставка, стоимость_заказ, id_курьер, действие_модератор) VALUES",
        "(139, 11, 1, 'в_процессе', '2024-12-18 05:54:48', "
        "'улица Ленина 3 Екатеринбург', '2024-12-25 10:10:00', 2439.00, 1, 'утвердить');",
        "",
        f"INSERT INTO ТоварыВЗаказе (id_заказа, id_товара, количество) VALUES (139, {melasti_i}, 1), (139, {pfc_i}, 1);",
        "",
        "INSERT INTO ИсторияЗаказов (id_заказы, статус_ИсторияЗаказов, дата_ИсторияЗаказов) VALUES",
        "(139, 'новый', '2024-12-18 05:54:48'), (139, 'в_процессе', '2024-12-18 06:10:00');",
        "",
        "INSERT INTO Маршрут (id_курьер, начальная_точка, конечная_точка, расстояние_маршрут, длительность_маршрут) VALUES",
        "(1, 'ул. Малышева, 71, Екатеринбург', 'улица Ленина 3 Екатеринбург', 4.20, 25);",
        "",
        "INSERT INTO ТочкиМаршрута (id_маршрут, координаты_ТочкиМаршрута, тип_ТочкиМаршрута, id_заказы) VALUES",
        "(1, '56.838011,60.597465', 'забрать', 139), (1, '56.835000,60.612000', 'доставить', 139);",
        "",
        "UPDATE Курьер SET текущие_заказы = 1 WHERE id_курьер = 1;",
        "",
        "SET FOREIGN_KEY_CHECKS = 1;",
    ]

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes), products={len(products)}")


if __name__ == "__main__":
    main()
