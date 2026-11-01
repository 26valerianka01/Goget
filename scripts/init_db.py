# init_db.py - создание БД и таблиц (если не используете Docker init)
import sys
from pathlib import Path

import mysql.connector
from mysql.connector import Error

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config.db import DB_NAME, connect_kwargs


def main():
    cfg = connect_kwargs(include_database=False)
    connection = mysql.connector.connect(**cfg)
    cursor = connection.cursor()
    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    cursor.execute(f"USE `{DB_NAME}`")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

    statements = [
        """
        CREATE TABLE IF NOT EXISTS Пользователи (
            id_пользователя INT PRIMARY KEY AUTO_INCREMENT,
            ФИО VARCHAR(255) NOT NULL,
            пароль VARCHAR(255) NOT NULL,
            эл_почта VARCHAR(255) UNIQUE NOT NULL,
            номер_телефона VARCHAR(20) UNIQUE NOT NULL,
            роль ENUM('клиент', 'курьер', 'модератор') NOT NULL DEFAULT 'клиент'
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Магазин (
            id_магазин INT PRIMARY KEY AUTO_INCREMENT,
            название_магазин VARCHAR(255) NOT NULL,
            адрес_магазин VARCHAR(255) NOT NULL,
            номер_тел_магазин VARCHAR(20),
            эл_почта_магазин VARCHAR(255)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Категория (
            id_категория INT PRIMARY KEY AUTO_INCREMENT,
            название_категория VARCHAR(255) NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Товары (
            id_товары INT PRIMARY KEY AUTO_INCREMENT,
            название_товары VARCHAR(255) NOT NULL,
            описание_товары TEXT,
            цена_товары DECIMAL(10,2) NOT NULL,
            id_магазин INT,
            id_категория INT,
            количество_товаров INT,
            путь_к_изображению TEXT,
            FOREIGN KEY (id_магазин) REFERENCES Магазин(id_магазин),
            FOREIGN KEY (id_категория) REFERENCES Категория(id_категория)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS КатегорияТовары (
            id_КатегорияТовары INT PRIMARY KEY AUTO_INCREMENT,
            id_категория INT,
            id_товары INT,
            FOREIGN KEY (id_категория) REFERENCES Категория(id_категория),
            FOREIGN KEY (id_товары) REFERENCES Товары(id_товары)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Курьер (
            id_курьер INT PRIMARY KEY,
            статус_курьер ENUM('доступен', 'недоступен') NOT NULL DEFAULT 'доступен',
            координаты_курьер TEXT,
            трансстредство_курьер VARCHAR(255),
            текущие_заказы INT DEFAULT 0,
            FOREIGN KEY (id_курьер) REFERENCES Пользователи(id_пользователя)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Заказы (
            id_заказы INT PRIMARY KEY AUTO_INCREMENT,
            id_пользователя INT,
            id_магазин INT,
            статус_заказ ENUM('новый', 'в_процессе', 'доставлен', 'отклонен') NOT NULL DEFAULT 'новый',
            датат_заказ DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            адрес_доставка VARCHAR(255) NOT NULL,
            время_доставка DATETIME,
            стоимость_заказ DECIMAL(10,2) NOT NULL,
            id_курьер INT,
            id_модератор INT,
            действие_модератор ENUM('утвердить', 'отклонить', 'отменить'),
            FOREIGN KEY (id_пользователя) REFERENCES Пользователи(id_пользователя),
            FOREIGN KEY (id_магазин) REFERENCES Магазин(id_магазин),
            FOREIGN KEY (id_курьер) REFERENCES Курьер(id_курьер),
            FOREIGN KEY (id_модератор) REFERENCES Пользователи(id_пользователя)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ТоварыВЗаказе (
            id_товары_в_заказе INT PRIMARY KEY AUTO_INCREMENT,
            id_заказа INT,
            id_товара INT,
            количество INT,
            FOREIGN KEY (id_заказа) REFERENCES Заказы(id_заказы),
            FOREIGN KEY (id_товара) REFERENCES Товары(id_товары)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ИсторияЗаказов (
            id_ИсторияЗаказов INT PRIMARY KEY AUTO_INCREMENT,
            id_заказы INT,
            статус_ИсторияЗаказов ENUM('новый', 'в_процессе', 'доставлен', 'отклонен') NOT NULL,
            дата_ИсторияЗаказов DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_заказы) REFERENCES Заказы(id_заказы)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Маршрут (
            id_маршрут INT PRIMARY KEY AUTO_INCREMENT,
            id_курьер INT,
            начальная_точка TEXT,
            конечная_точка TEXT,
            расстояние_маршрут DECIMAL(10,2) NOT NULL,
            длительность_маршрут INT NOT NULL,
            FOREIGN KEY (id_курьер) REFERENCES Курьер(id_курьер)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ТочкиМаршрута (
            id_ТочкиМаршрута INT PRIMARY KEY AUTO_INCREMENT,
            id_маршрут INT,
            координаты_ТочкиМаршрута TEXT,
            тип_ТочкиМаршрута ENUM('забрать', 'доставить') NOT NULL,
            id_заказы INT,
            FOREIGN KEY (id_маршрут) REFERENCES Маршрут(id_маршрут),
            FOREIGN KEY (id_заказы) REFERENCES Заказы(id_заказы)
        )
        """,
    ]

    for sql in statements:
        cursor.execute(sql)

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    connection.commit()
    cursor.execute("SHOW TABLES")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"OK: база {DB_NAME} готова")
    print("Таблицы:", ", ".join(tables))
    cursor.close()
    connection.close()


if __name__ == "__main__":
    try:
        main()
    except Error as e:
        print("Ошибка:", e)
