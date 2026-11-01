"""Управление пользователями: регистрация, вход, проверка БД."""
from __future__ import annotations

import logging

import mysql.connector
from mysql.connector import Error
from tkinter import messagebox

from app.auth.passwords import hash_password, needs_rehash, verify_password
from app.config.db import DB_HOST, DB_NAME, DB_PORT, DB_USER, connect_kwargs

logger = logging.getLogger("goget.auth")


class UserManager:
    _instance = None
    current_user_id = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(UserManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def create_database(self):
        """Проверяет соединение с БД и наличие таблицы пользователей."""
        connection = None
        try:
            connection = mysql.connector.connect(**connect_kwargs(True))
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS Пользователи (
                    id_пользователя INT PRIMARY KEY AUTO_INCREMENT,
                    ФИО VARCHAR(255) NOT NULL,
                    пароль VARCHAR(255) NOT NULL,
                    эл_почта VARCHAR(255) UNIQUE NOT NULL,
                    номер_телефона VARCHAR(20) UNIQUE NOT NULL,
                    роль ENUM('клиент', 'курьер', 'модератор') NOT NULL DEFAULT 'клиент'
                )
                """
            )
            connection.commit()
            cursor.close()
            logger.info("DB connection OK (%s@%s:%s/%s)", DB_USER, DB_HOST, DB_PORT, DB_NAME)
        except Error as e:
            logger.exception("DB connection failed: %s", e)
            hint = (
                f"\n\nСейчас: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}\n"
                "1) Запустите Docker Desktop\n"
                "2) Выполните: docker compose up -d\n"
                "3) Или дважды кликните start.bat"
            )
            messagebox.showerror("Ошибка", f"Нет подключения к базе данных.{hint}")
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()

    def register_user(self, full_name, password, email, phone_number):
        connection = None
        try:
            connection = mysql.connector.connect(**connect_kwargs(True))
            cursor = connection.cursor()

            cursor.execute(
                "SELECT id_пользователя FROM Пользователи WHERE номер_телефона=%s OR эл_почта=%s",
                (phone_number, email),
            )
            if cursor.fetchone():
                messagebox.showerror(
                    "Ошибка",
                    "Пользователь с таким номером телефона или эл. почтой уже существует.",
                )
                return

            hashed = hash_password(password)
            cursor.execute(
                "INSERT INTO Пользователи (ФИО, пароль, эл_почта, номер_телефона) VALUES (%s, %s, %s, %s)",
                (full_name, hashed, email, phone_number),
            )
            connection.commit()
            logger.info("Registered user %s", email)
            messagebox.showinfo("Успех", "Регистрация прошла успешно!")
        except Error as e:
            logger.exception("Registration failed: %s", e)
            messagebox.showerror("Ошибка", "Не удалось зарегистрировать пользователя. Подробности в logs/app.log")
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def login_user(self, email_or_phone, password):
        connection = None
        try:
            connection = mysql.connector.connect(**connect_kwargs(True))
            cursor = connection.cursor()

            cursor.execute(
                "SELECT id_пользователя, роль, пароль FROM Пользователи "
                "WHERE эл_почта=%s OR номер_телефона=%s",
                (email_or_phone, email_or_phone),
            )
            user = cursor.fetchone()
            if not user:
                return None

            user_id, role, stored = user
            if not verify_password(password, stored):
                return None

            if needs_rehash(stored):
                try:
                    cursor.execute(
                        "UPDATE Пользователи SET пароль=%s WHERE id_пользователя=%s",
                        (hash_password(password), user_id),
                    )
                    connection.commit()
                    logger.info("Rehashed legacy password for user id=%s", user_id)
                except Error as e:
                    logger.warning("Could not rehash password for id=%s: %s", user_id, e)

            self.current_user_id = user_id
            logger.info("Login ok id=%s role=%s", user_id, role)
            return role
        except Error as e:
            logger.exception("Login failed: %s", e)
            messagebox.showerror("Ошибка", "Ошибка при входе. Подробности в logs/app.log")
            return None
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def get_current_user_id(self):
        return self.current_user_id
