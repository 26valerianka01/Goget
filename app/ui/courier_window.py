# courier_window.py - интерфейс курьера в стиле макетов GoGet
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from mysql.connector import Error
from tkinter import messagebox
from app.db.catalog import get_connection
from app.ui.courier_map_display import display_courier_map
from app.auth.users import UserManager
from tkinter.constants import BOTH, CENTER
from app.ui.theme import (
    create_app_root,
    create_app_toplevel,
    apply_goget_styles,
    build_header,
    themed_card,
    pink_button,
    LAVENDER_BG,
    WHITE,
    ACCENT_PINK,
    TEXT_DARK,
    PURPLE_HEADER,
    FONT_TITLE,
    MUTED,
    LINE,
)

user_manager = UserManager()


def configure_courier_window(root):
    courier_id = user_manager.get_current_user_id()
    root.title("GoGet - Курьер")
    root.geometry("1600x960")
    root.resizable(False, False)

    for widget in root.winfo_children():
        widget.destroy()

    style = root.style if hasattr(root, "style") else ttk.Style()
    apply_goget_styles(style)

    try:
        icon_img = Image.open("assets/icon.png")
        icon_photo = ImageTk.PhotoImage(icon_img)
        root.iconphoto(False, icon_photo)
        root._icon = icon_photo
    except FileNotFoundError:
        print("Иконка не найдена")

    content_frame = tk.Frame(root, bg=LAVENDER_BG)

    def clear_content_frame():
        for widget in content_frame.winfo_children():
            widget.destroy()

    def on_orders_click():
        clear_content_frame()
        set_active("orders")
        main_frame = tk.Frame(content_frame, bg=LAVENDER_BG)
        main_frame.pack(fill="both", expand=True, padx=60, pady=16)

        card = themed_card(main_frame)
        card.pack(fill="both", expand=True)

        tk.Label(card, text="Ваши заказы", bg=WHITE, fg=TEXT_DARK, font=("Segoe UI", 16, "bold")).pack(
            anchor="w", padx=20, pady=(16, 8)
        )

        columns = [
            "Идентификатор заказа",
            "Дата и время создания заказа",
            "Желаемое время доставки",
            "Стоимость заказа",
            "Статус заказа",
        ]
        orders_tree = ttk.Treeview(card, columns=columns, show="headings", height=15)
        for col in columns:
            orders_tree.heading(col, text=col)
            orders_tree.column(col, width=280, anchor=CENTER)
        orders_tree.pack(fill=BOTH, expand=True, padx=16, pady=8)

        def on_mouse_wheel(event):
            try:
                if orders_tree.winfo_exists():
                    orders_tree.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass

        orders_tree.bind("<MouseWheel>", on_mouse_wheel)
        load_assigned_orders(orders_tree, courier_id)

        status_enabled = {"ok": True}

        def on_select(event):
            selected_item = orders_tree.selection()
            if selected_item:
                current_status = orders_tree.item(selected_item[0], "values")[4]
                status_enabled["ok"] = current_status == "в_процессе"
                fg = WHITE if status_enabled["ok"] else MUTED
                bg = ACCENT_PINK if status_enabled["ok"] else LINE
                change_status_button.configure(bg=bg)
                change_status_button._label.configure(bg=bg, fg=fg)

        orders_tree.bind("<ButtonRelease-1>", on_select)

        def _change():
            if status_enabled["ok"]:
                change_order_status(orders_tree, courier_id)

        change_status_button = pink_button(
            main_frame,
            "Изменить статус",
            _change,
            fill=True,
            pady=12,
        )

    def on_map_click():
        clear_content_frame()
        set_active("map")
        display_courier_map(content_frame, courier_id)

    def on_profile_click():
        clear_content_frame()
        set_active("profile")
        display_profile(content_frame, courier_id)

    _, set_active = build_header(
        root,
        [
            ("orders", "Заказы", on_orders_click),
            ("map", "Карта", on_map_click),
            ("profile", "Профиль", on_profile_click),
        ],
        active_key="orders",
    )
    content_frame.pack(expand=True, fill="both")
    on_orders_click()


def load_assigned_orders(tree, courier_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id_заказы, датат_заказ, время_доставка, стоимость_заказ, статус_заказ "
            "FROM Заказы WHERE id_курьер = %s",
            (courier_id,),
        )
        for order in cursor.fetchall():
            tree.insert("", "end", values=order)
    except Error as e:
        messagebox.showerror("Ошибка", f"Ошибка при загрузке заказов: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def change_order_status(tree, courier_id):
    selected_item = tree.selection()
    if selected_item:
        selected_item = selected_item[0]
        order_id = tree.item(selected_item, "values")[0]
        current_status = tree.item(selected_item, "values")[4]

        if current_status == "в_процессе":
            new_status = "доставлен"
            try:
                connection = get_connection()
                cursor = connection.cursor()
                cursor.execute(
                    "UPDATE Заказы SET статус_заказ = %s WHERE id_заказы = %s",
                    (new_status, order_id),
                )
                connection.commit()
                # В Docker/Linux имена таблиц чувствительны к регистру
                cursor.execute(
                    "SELECT DISTINCT id_маршрут FROM ТочкиМаршрута WHERE id_заказы = %s",
                    (order_id,),
                )
                route_ids = cursor.fetchall()
                cursor.execute("DELETE FROM ТочкиМаршрута WHERE id_заказы = %s", (order_id,))
                connection.commit()
                for route_id in route_ids:
                    cursor.execute("DELETE FROM Маршрут WHERE id_маршрут = %s", (route_id[0],))
                connection.commit()
                from app.ui.order_window import sync_courier_load

                sync_courier_load(courier_id)
                tree.item(
                    selected_item,
                    values=(
                        order_id,
                        tree.item(selected_item, "values")[1],
                        tree.item(selected_item, "values")[2],
                        tree.item(selected_item, "values")[3],
                        new_status,
                    ),
                )
                messagebox.showinfo("Успех", "Статус заказа успешно изменен")
            except Error as e:
                messagebox.showerror("Ошибка", f"Ошибка при изменении статуса заказа: {e}")
            finally:
                if connection.is_connected():
                    cursor.close()
                    connection.close()
        else:
            messagebox.showwarning("Предупреждение", "Статус заказа не может быть изменен")


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


def display_profile(content_frame, courier_id):
    user_data = get_user_data(courier_id)
    card = themed_card(content_frame)
    card.place(relx=0.5, rely=0.5, anchor="center", width=720, height=360)
    tk.Label(card, text="Профиль", bg=WHITE, fg=PURPLE_HEADER, font=FONT_TITLE).pack(
        anchor="w", padx=40, pady=(28, 16)
    )
    if not user_data:
        tk.Label(card, text="Данные пользователя не найдены", bg=WHITE, fg="#666", font=("Segoe UI", 13)).pack(
            padx=40
        )
        return
    fields = [
        ("ФИО:", user_data[0]),
        ("Email:", user_data[2]),
        ("Номер телефона:", user_data[3]),
        ("Роль:", user_data[4]),
    ]
    for label, value in fields:
        row = tk.Frame(card, bg=WHITE)
        row.pack(fill="x", padx=40, pady=8)
        tk.Label(row, text=label, bg=WHITE, fg=TEXT_DARK, font=("Segoe UI", 13), width=18, anchor="w").pack(
            side="left"
        )
        tk.Label(row, text=str(value), bg=WHITE, fg=TEXT_DARK, font=("Segoe UI", 13)).pack(side="left")


if __name__ == "__main__":
    root = create_app_root()
    configure_courier_window(root)
    root.mainloop()
