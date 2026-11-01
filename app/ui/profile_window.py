# profile_window.py
import tkinter as tk
from app.db.catalog import get_connection
from mysql.connector import Error
from app.ui.theme import surface_card, SURFACE, INK, MUTED, BG, FONT_TITLE, FONT_BODY, FONT_MUTED


def get_user_data(user_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT ФИО, пароль, эл_почта, номер_телефона, роль FROM Пользователи WHERE id_пользователя = %s",
            (user_id,),
        )
        return cursor.fetchone()
    except Error as e:
        print(f"Ошибка при получении данных пользователя: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def display_profile(content_frame, user_id):
    for w in content_frame.winfo_children():
        w.destroy()
    try:
        content_frame.configure(bg=BG)
    except Exception:
        pass

    user_data = get_user_data(user_id)
    card = surface_card(content_frame)
    card.place(relx=0.5, rely=0.5, anchor="center", width=640, height=360)

    tk.Label(card, text="Профиль", bg=SURFACE, fg=INK, font=FONT_TITLE).pack(anchor="w", padx=36, pady=(28, 8))
    if not user_data:
        tk.Label(card, text="Данные не найдены", bg=SURFACE, fg=MUTED, font=FONT_BODY).pack(padx=36)
        return

    for label, value in (
        ("ФИО", user_data[0]),
        ("Email", user_data[2]),
        ("Телефон", user_data[3]),
        ("Роль", user_data[4]),
    ):
        row = tk.Frame(card, bg=SURFACE)
        row.pack(fill="x", padx=36, pady=8)
        tk.Label(row, text=label, bg=SURFACE, fg=MUTED, font=FONT_MUTED, width=12, anchor="w").pack(side="left")
        tk.Label(row, text=str(value), bg=SURFACE, fg=INK, font=FONT_BODY).pack(side="left")
