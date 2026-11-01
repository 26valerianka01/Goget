# order_window.py - оформление и список заказов
import re
import tkinter as tk
from tkinter import messagebox

from tkinter import ttk
from mysql.connector import Error
from PIL import Image, ImageTk

from app.db.catalog import get_connection
from app.services.cart import cart_items
from app.services.routing import create_route_with_points
from app.auth.users import UserManager
from app.ui.theme import (
    create_app_root,
    create_app_toplevel,
    BG,
    SURFACE,
    INK,
    MUTED,
    ACCENT,
    ACCENT_HOVER,
    LINE,
    WHITE,
    FONT_TITLE,
    FONT_H2,
    FONT_BODY,
    FONT_MUTED,
    FONT_BTN,
    FONT_PRICE,
    surface_card,
    soft_button,
)

user_manager = UserManager()


def create_order_window(content_frame):
    order_window = create_app_toplevel()
    order_window.title("Оформление заказа")
    order_window.geometry("720x780")
    order_window.resizable(False, False)
    order_window.grab_set()
    order_window.configure(bg=BG)

    try:
        icon_photo = ImageTk.PhotoImage(Image.open("assets/icon.png"))
        order_window.iconphoto(False, icon_photo)
        order_window._icon = icon_photo
    except FileNotFoundError:
        pass

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT ФИО, номер_телефона, эл_почта FROM Пользователи WHERE id_пользователя = %s",
            (user_manager.get_current_user_id(),),
        )
        user_info = cursor.fetchone()
    except Error as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить профиль: {e}")
        order_window.destroy()
        return
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    if not user_info:
        messagebox.showerror("Ошибка", "Профиль не найден.")
        order_window.destroy()
        return

    body = tk.Frame(order_window, bg=BG)
    body.pack(fill="both", expand=True, padx=28, pady=24)

    tk.Label(body, text="Оформление заказа", bg=BG, fg=INK, font=FONT_TITLE).pack(anchor="w")
    tk.Label(body, text=f"{user_info[0]} · {user_info[1]}", bg=BG, fg=MUTED, font=FONT_MUTED).pack(
        anchor="w", pady=(4, 12)
    )

    total_cost = sum(item["quantity"] * float(item["product"][3]) for item in cart_items)
    tk.Label(body, text=f"К оплате: {total_cost:.2f} ₽", bg=BG, fg=INK, font=FONT_PRICE).pack(anchor="w")

    from app.ui.scroll import make_scrollable

    list_wrap = tk.Frame(body, bg=BG, height=240)
    list_wrap.pack(fill="both", expand=True, pady=12)
    list_wrap.pack_propagate(False)
    _, _canvas, scrollable = make_scrollable(list_wrap, bg=BG)

    for item in cart_items:
        product = item["product"]
        quantity = item["quantity"]
        row = surface_card(scrollable)
        row.pack(fill="x", pady=4)
        tk.Label(row, text=f"{product[1]} × {quantity}", bg=SURFACE, fg=INK, font=FONT_BODY).pack(
            side="left", padx=12, pady=10
        )
        tk.Label(
            row,
            text=f"{quantity * float(product[3]):.2f} ₽",
            bg=SURFACE,
            fg=MUTED,
            font=FONT_MUTED,
        ).pack(side="right", padx=12)

    form = tk.Frame(body, bg=BG)
    form.pack(fill="x", pady=8)
    tk.Label(form, text="Адрес доставки", bg=BG, fg=MUTED, font=FONT_MUTED).pack(anchor="w")
    address_entry = tk.Entry(form, font=FONT_BODY, relief="flat", highlightthickness=1, highlightbackground=LINE)
    address_entry.pack(fill="x", pady=(4, 10), ipady=8)
    tk.Label(form, text="Желаемое время (YYYY-MM-DD HH:MM)", bg=BG, fg=MUTED, font=FONT_MUTED).pack(anchor="w")
    time_entry = tk.Entry(form, font=FONT_BODY, relief="flat", highlightthickness=1, highlightbackground=LINE)
    time_entry.pack(fill="x", pady=(4, 10), ipady=8)

    soft_button(
        body,
        "Подтвердить заказ",
        lambda: confirm_order(address_entry.get(), time_entry.get(), total_cost, order_window, content_frame),
        primary=True,
        fill="x",
        pady=(8, 0),
    )


def confirm_order(address, time, total_cost, order_window, content_frame):
    if not address or not time:
        messagebox.showerror("Ошибка", "Заполните адрес и время доставки.")
        return
    if not re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", time):
        messagebox.showerror("Ошибка", "Формат времени: YYYY-MM-DD HH:MM")
        return
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO Заказы (id_пользователя, статус_заказ, адрес_доставка, время_доставка, стоимость_заказ) "
            "VALUES (%s, %s, %s, %s, %s)",
            (user_manager.get_current_user_id(), "новый", address, time, total_cost),
        )
        connection.commit()
        order_id = cursor.lastrowid
        for item in cart_items:
            cursor.execute(
                "INSERT INTO ТоварыВЗаказе (id_заказа, id_товара, количество) VALUES (%s, %s, %s)",
                (order_id, item["product"][0], item["quantity"]),
            )
        connection.commit()
        cart_items.clear()
        messagebox.showinfo("Готово", "Заказ оформлен!")
        order_window.destroy()
        update_orders_tab(content_frame)
        create_route_with_points(order_id, address)
    except Error as e:
        messagebox.showerror("Ошибка", f"Не удалось оформить заказ: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def update_orders_tab(content_frame):
    for widget in content_frame.winfo_children():
        widget.destroy()

    wrap = tk.Frame(content_frame, bg=BG)
    wrap.pack(fill="both", expand=True, padx=48, pady=24)
    tk.Label(wrap, text="Мои заказы", bg=BG, fg=INK, font=FONT_TITLE).pack(anchor="w")
    tk.Label(wrap, text="Статус обновляется после действий модератора и курьера", bg=BG, fg=MUTED, font=FONT_MUTED).pack(
        anchor="w", pady=(4, 16)
    )

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id_заказы, адрес_доставка, время_доставка, стоимость_заказ, статус_заказ "
            "FROM Заказы WHERE id_пользователя = %s ORDER BY id_заказы DESC",
            (user_manager.get_current_user_id(),),
        )
        orders = cursor.fetchall()
        if not orders:
            tk.Label(wrap, text="Заказов пока нет", bg=BG, fg=MUTED, font=FONT_BODY).pack(anchor="w", pady=24)
            return

        status_color = {
            "новый": "#2563EB",
            "в_процессе": "#D97706",
            "доставлен": "#059669",
            "отклонён": "#DC2626",
            "отклонен": "#DC2626",
            "отменён": "#DC2626",
            "отменен": "#DC2626",
        }

        for order in orders:
            order_id, address, time, total_cost, status = order
            card = surface_card(wrap)
            card.pack(fill="x", pady=8)

            left = tk.Frame(card, bg=SURFACE)
            left.pack(side="left", fill="x", expand=True, padx=20, pady=16)
            tk.Label(left, text=f"Заказ №{order_id}", bg=SURFACE, fg=INK, font=FONT_H2).pack(anchor="w")
            tk.Label(left, text=f"{address} · {time}", bg=SURFACE, fg=MUTED, font=FONT_MUTED).pack(anchor="w", pady=(4, 0))
            tk.Label(left, text=f"{total_cost} ₽", bg=SURFACE, fg=INK, font=FONT_PRICE).pack(anchor="w", pady=(8, 0))

            right = tk.Frame(card, bg=SURFACE)
            right.pack(side="right", padx=20, pady=16)
            color = status_color.get(str(status).lower(), MUTED)
            tk.Label(right, text=str(status), bg=SURFACE, fg=color, font=FONT_BTN).pack(anchor="e")
            soft_button(right, "Подробнее", lambda o=order: show_order_details(o), primary=False, pady=(10, 0))
    except Error as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить заказы: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def show_order_details(order):
    order_id, address, time, total_cost, status = order
    win = create_app_toplevel()
    win.title(f"Заказ №{order_id}")
    win.geometry("720x700")
    win.configure(bg=BG)

    body = tk.Frame(win, bg=BG)
    body.pack(fill="both", expand=True, padx=28, pady=24)
    tk.Label(body, text=f"Заказ №{order_id}", bg=BG, fg=INK, font=FONT_TITLE).pack(anchor="w")
    tk.Label(body, text=f"Статус: {status}", bg=BG, fg=MUTED, font=FONT_MUTED).pack(anchor="w", pady=(4, 12))

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT t.название_товары, t.цена_товары, t.путь_к_изображению, tvz.количество
            FROM Товары t
            JOIN ТоварыВЗаказе tvz ON t.id_товары = tvz.id_товара
            WHERE tvz.id_заказа = %s
            """,
            (order_id,),
        )
        products = cursor.fetchall()
    except Error as e:
        messagebox.showerror("Ошибка", str(e))
        win.destroy()
        return
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    for name, price, path, qty in products:
        row = surface_card(body)
        row.pack(fill="x", pady=4)
        try:
            photo = ImageTk.PhotoImage(Image.open(str(path).strip('"')).resize((48, 48), Image.LANCZOS))
            lbl = tk.Label(row, image=photo, bg=SURFACE)
            lbl.image = photo
            lbl.pack(side="left", padx=10, pady=8)
        except Exception:
            pass
        tk.Label(row, text=f"{name} × {qty}", bg=SURFACE, fg=INK, font=FONT_BODY).pack(side="left", padx=8)
        tk.Label(row, text=f"{float(price) * qty:.2f} ₽", bg=SURFACE, fg=MUTED, font=FONT_MUTED).pack(
            side="right", padx=12
        )

    tk.Label(body, text=f"Итого: {total_cost} ₽", bg=BG, fg=INK, font=FONT_PRICE).pack(anchor="w", pady=(16, 4))
    tk.Label(body, text=f"Адрес: {address}", bg=BG, fg=MUTED, font=FONT_MUTED).pack(anchor="w")
    tk.Label(body, text=f"Время: {time}", bg=BG, fg=MUTED, font=FONT_MUTED).pack(anchor="w")


def get_couriers():
    """Курьеры, у которых сейчас меньше 2 активных заказов (статус в_процессе)."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT p.id_пользователя, p.ФИО,
                   (SELECT COUNT(*) FROM Заказы z
                    WHERE z.id_курьер = k.id_курьер AND z.статус_заказ = 'в_процессе') AS active_cnt
            FROM Пользователи p
            JOIN Курьер k ON p.id_пользователя = k.id_курьер
            WHERE p.роль = 'курьер'
              AND k.статус_курьер = 'доступен'
              AND (SELECT COUNT(*) FROM Заказы z
                   WHERE z.id_курьер = k.id_курьер AND z.статус_заказ = 'в_процессе') < 2
            ORDER BY active_cnt ASC, p.ФИО
            """
        )
        return [(row[0], f"{row[1]} ({row[2]}/2)") for row in cursor.fetchall()]
    except Error as e:
        print(f"Ошибка при получении курьеров: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def sync_courier_load(courier_id):
    """Синхронизирует текущие_заказы с реальным числом заказов в_процессе."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM Заказы WHERE id_курьер=%s AND статус_заказ='в_процессе'",
            (courier_id,),
        )
        cnt = cursor.fetchone()[0]
        cursor.execute(
            "UPDATE Курьер SET текущие_заказы=%s WHERE id_курьер=%s",
            (cnt, courier_id),
        )
        connection.commit()
        return cnt
    except Error as e:
        print(f"Ошибка sync_courier_load: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
