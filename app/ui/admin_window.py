import tkinter as tk
from app.db.catalog import get_connection
from mysql.connector import Error
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk
from app.ui.order_management import load_orders, update_order_status, on_select, load_new_orders
from app.auth.users import UserManager
from app.db.order_queries import get_all_orders, get_new_orders, get_delivered_orders, get_cancelled_orders, get_stores_from_order
from app.ui.map_display import display_map
from app.ui.order_window import get_couriers, sync_courier_load
from app.services.routing import insert_route
from app.ui.user_window import configure_users_window
from app.ui.store_window import configure_stores_window
from app.ui.item_window import configure_items_window
from app.ui.profile_window import display_profile
from tkinter.constants import BOTH, CENTER, BOTTOM
from app.ui.theme import (
    create_app_root,
    create_app_toplevel,
    apply_goget_styles,
    build_header,
    themed_card,
    pink_button,
    soft_button,
    LAVENDER_BG,
    WHITE,
    ACCENT_PINK,
    TEXT_DARK,
)

user_manager = UserManager()


def _safe_mousewheel(tree):
    def on_mouse_wheel(event):
        try:
            if tree.winfo_exists():
                tree.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass
    return on_mouse_wheel


def assign_courier_to_route(order_id, courier_id, tree, selected_item):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT статус_курьер FROM Курьер WHERE id_курьер = %s", (courier_id,))
        result = cursor.fetchone()
        if not result:
            messagebox.showerror("Ошибка", "Курьер не найден.")
            return
        if result[0] != "доступен":
            messagebox.showerror("Ошибка", "Этот курьер недоступен.")
            return
        # Живой счётчик: занят, если уже 2 заказа «в_процессе»
        cursor.execute(
            "SELECT COUNT(*) FROM Заказы WHERE id_курьер=%s AND статус_заказ='в_процессе'",
            (courier_id,),
        )
        active = cursor.fetchone()[0]
        if active >= 2:
            messagebox.showerror(
                "Ошибка",
                "У курьера уже 2 активных заказа. Назначьте после доставки одного из них.",
            )
            return

        cursor.execute(
            "UPDATE Заказы SET id_курьер = %s, статус_заказ = 'в_процессе' WHERE id_заказы = %s",
            (courier_id, order_id),
        )
        connection.commit()

        cursor.execute(
            "SELECT координаты_ТочкиМаршрута, тип_ТочкиМаршрута FROM ТочкиМаршрута WHERE id_заказы = %s",
            (order_id,),
        )
        route_points = cursor.fetchall()
        if route_points:
            start_point = route_points[0][0]
            end_point = route_points[-1][0]
            # расстояние пересчитает create_route / insert с 0 - оставляем связь
            from app.services.routing import get_distance

            dist = 0.0
            for i in range(len(route_points) - 1):
                dist += get_distance(route_points[i][0], route_points[i + 1][0])
            if dist >= 1e8:
                dist = 0.0
            duration = int(dist / 25 * 60) + 10 * len(route_points)  # ~25 км/ч + 10 мин на точку
            route_id = insert_route(courier_id, start_point, end_point, round(dist, 2), duration)
            cursor.execute(
                "UPDATE ТочкиМаршрута SET id_маршрут = %s WHERE id_заказы = %s",
                (route_id, order_id),
            )
            connection.commit()

        sync_courier_load(courier_id)
        cursor.execute("SELECT ФИО FROM Пользователи WHERE id_пользователя = %s", (courier_id,))
        courier_name = cursor.fetchone()[0]
        values = list(tree.item(selected_item, "values"))
        if len(values) >= 6:
            values[5] = courier_name
            tree.item(selected_item, values=values)
        messagebox.showinfo("Успех", "Курьер назначен успешно!")
    except Error as e:
        messagebox.showerror("Ошибка", f"Ошибка при назначении курьера: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def configure_admin_window(root, initial_load=False):
    root.title("GoGet - Модератор")
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

        tk.Label(
            card,
            text="Последние 20 заказов",
            bg=WHITE,
            fg=TEXT_DARK,
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w", padx=20, pady=(16, 8))

        columns = [
            "Идентификатор заказа",
            "Дата и время создания заказа",
            "Желаемое время доставки",
            "Статус заказа",
            "Тип действия модератора",
        ]

        orders_tree = ttk.Treeview(card, columns=columns, show="headings", height=14)
        for col in columns:
            orders_tree.heading(col, text=col)
            orders_tree.column(col, width=280, anchor=CENTER)
        orders_tree.pack(fill=BOTH, expand=True, padx=16, pady=8)
        orders_tree.bind("<MouseWheel>", _safe_mousewheel(orders_tree))

        controls = tk.Frame(card, bg=WHITE)
        controls.pack(fill="x", padx=16, pady=(4, 8))

        action_var = tk.StringVar(value="утвердить")
        tk.Label(controls, text="Действие при выборе строки:", bg=WHITE, fg=TEXT_DARK, font=("Segoe UI", 11)).pack(
            side="left"
        )
        action_menu = ttk.OptionMenu(controls, action_var, "утвердить", "утвердить", "отклонить", "отменить")
        action_menu.pack(side="left", padx=8)

        orders_tree.bind("<<TreeviewSelect>>", lambda event: on_select(event, orders_tree, action_var, user_manager))

        # Переключатель: все последние / только новые
        is_showing_new_orders = False

        def on_filter_click():
            nonlocal is_showing_new_orders
            if is_showing_new_orders:
                load_orders(orders_tree)
                filter_btn._label.configure(text="Показать только новые")
                is_showing_new_orders = False
            else:
                load_new_orders(orders_tree)
                filter_btn._label.configure(text="Показать все (20)")
                is_showing_new_orders = True

        filter_btn = soft_button(
            controls,
            "Показать только новые",
            on_filter_click,
            primary=False,
            side="right",
        )

        footer = tk.Frame(main_frame, bg=LAVENDER_BG)
        footer.pack(fill="x", pady=12)
        pink_button(footer, "Перейти к заказам (назначить курьера / карта)", show_all_orders_window, fill=True)
        load_orders(orders_tree)

    def on_users_click():
        clear_content_frame()
        set_active("users")
        configure_users_window(content_frame)

    def on_stores_click():
        clear_content_frame()
        set_active("stores")
        configure_stores_window(content_frame)

    def on_items_click():
        clear_content_frame()
        set_active("items")
        configure_items_window(content_frame)

    def on_profile_click():
        clear_content_frame()
        set_active("profile")
        display_profile(content_frame, user_manager.get_current_user_id())

    # В макетах 5-й пункт «Статистика»; в приложении это профиль модератора
    _, set_active = build_header(
        root,
        [
            ("orders", "Заказы", on_orders_click),
            ("users", "Пользователи", on_users_click),
            ("stores", "Магазины", on_stores_click),
            ("items", "Товары", on_items_click),
            ("profile", "Профиль", on_profile_click),
        ],
        active_key="orders",
    )
    content_frame.pack(expand=True, fill="both")

    if initial_load:
        on_orders_click()


def show_all_orders_window():
    orders_window = create_app_toplevel()
    orders_window.title("Все заказы")
    orders_window.geometry("1600x960")
    orders_window.grab_set()
    orders_window.resizable(False, False)

    try:
        icon_img = Image.open("assets/icon.png")
        icon_photo = ImageTk.PhotoImage(icon_img)
        orders_window.iconphoto(False, icon_photo)
    except FileNotFoundError:
        print("Иконка не найдена")

    notebook = ttk.Notebook(orders_window)
    notebook.pack(expand=1, fill="both")

    all_orders_frame = ttk.Frame(notebook)
    notebook.add(all_orders_frame, text="Все заказы")

    new_orders_frame = ttk.Frame(notebook)
    notebook.add(new_orders_frame, text="Новые заказы")

    delivered_orders_frame = ttk.Frame(notebook)
    notebook.add(delivered_orders_frame, text="Доставленные заказы")

    cancelled_orders_frame = ttk.Frame(notebook)
    notebook.add(cancelled_orders_frame, text="Отмененные заказы")

    map_frame = ttk.Frame(notebook)
    notebook.add(map_frame, text="Карта")

    columns = ["Идентификатор заказа", "Товары", "Магазины", "Адрес доставки", "Желаемое время доставки", "Курьер"]

    def populate_treeview(tree, orders):
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 14), background="white", foreground="black")
        style.configure("Treeview", rowheight=40)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=247, anchor=CENTER)
        for order in orders:
            tree.insert("", "end", values=order)
        tree.bind("<MouseWheel>", _safe_mousewheel(tree))

    def assign_courier(tree, courier_var):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите заказ.")
            return
        order_id = tree.item(selected_item[0], "values")[0]
        courier_id = courier_var.get()
        if not courier_id or courier_id == "Выберите курьера":
            messagebox.showerror("Ошибка", "Пожалуйста, выберите курьера.")
            return
        assign_courier_to_route(order_id, courier_id, tree, selected_item[0])

    def populate_courier_menu(courier_menu, courier_var):
        couriers = get_couriers()
        courier_menu["menu"].delete(0, "end")
        for courier in couriers:
            courier_menu["menu"].add_command(label=courier[1], command=lambda c=courier[0]: courier_var.set(c))

    all_orders_tree = ttk.Treeview(all_orders_frame, columns=columns, show="headings", height=15)
    all_orders_tree.pack(fill=BOTH, expand=True, pady=10)
    populate_treeview(all_orders_tree, get_all_orders_with_stores())
    all_orders_courier_var = tk.StringVar()
    all_orders_courier_menu = ttk.OptionMenu(all_orders_frame, all_orders_courier_var, "Выберите курьера")
    all_orders_courier_menu.pack(side=BOTTOM, pady=10)
    populate_courier_menu(all_orders_courier_menu, all_orders_courier_var)
    ttk.Button(
        all_orders_frame, text="Назначить курьера", command=lambda: assign_courier(all_orders_tree, all_orders_courier_var)
    ).pack(side=BOTTOM, pady=10)

    new_orders_tree = ttk.Treeview(new_orders_frame, columns=columns, show="headings", height=15)
    new_orders_tree.pack(fill=BOTH, expand=True, pady=10)
    populate_treeview(new_orders_tree, get_new_orders_with_stores())
    new_orders_courier_var = tk.StringVar()
    new_orders_courier_menu = ttk.OptionMenu(new_orders_frame, new_orders_courier_var, "Выберите курьера")
    new_orders_courier_menu.pack(side=BOTTOM, pady=10)
    populate_courier_menu(new_orders_courier_menu, new_orders_courier_var)
    ttk.Button(
        new_orders_frame, text="Назначить курьера", command=lambda: assign_courier(new_orders_tree, new_orders_courier_var)
    ).pack(side=BOTTOM, pady=10)

    delivered_orders_tree = ttk.Treeview(delivered_orders_frame, columns=columns, show="headings", height=15)
    delivered_orders_tree.pack(fill=BOTH, expand=True, pady=10)
    populate_treeview(delivered_orders_tree, get_delivered_orders_with_stores())
    delivered_orders_courier_var = tk.StringVar()
    delivered_orders_courier_menu = ttk.OptionMenu(delivered_orders_frame, delivered_orders_courier_var, "Выберите курьера")
    delivered_orders_courier_menu.pack(side=BOTTOM, pady=10)
    populate_courier_menu(delivered_orders_courier_menu, delivered_orders_courier_var)
    ttk.Button(
        delivered_orders_frame,
        text="Назначить курьера",
        command=lambda: assign_courier(delivered_orders_tree, delivered_orders_courier_var),
    ).pack(side=BOTTOM, pady=10)

    cancelled_orders_tree = ttk.Treeview(cancelled_orders_frame, columns=columns, show="headings", height=15)
    cancelled_orders_tree.pack(fill=BOTH, expand=True, pady=10)
    populate_treeview(cancelled_orders_tree, get_cancelled_orders_with_stores())
    cancelled_orders_courier_var = tk.StringVar()
    cancelled_orders_courier_menu = ttk.OptionMenu(cancelled_orders_frame, cancelled_orders_courier_var, "Выберите курьера")
    cancelled_orders_courier_menu.pack(side=BOTTOM, pady=10)
    populate_courier_menu(cancelled_orders_courier_menu, cancelled_orders_courier_var)
    ttk.Button(
        cancelled_orders_frame,
        text="Назначить курьера",
        command=lambda: assign_courier(cancelled_orders_tree, cancelled_orders_courier_var),
    ).pack(side=BOTTOM, pady=10)

    def show_map():
        try:
            display_map(map_frame)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть карту: {e}")

    ttk.Button(map_frame, text="Посмотреть карту", command=show_map).pack(pady=10)


def get_all_orders_with_stores():
    orders = get_all_orders()
    return [(order[0], order[1], get_stores_from_order(order[0]), order[2], order[3], order[4]) for order in orders]


def get_new_orders_with_stores():
    orders = get_new_orders()
    return [(order[0], order[1], get_stores_from_order(order[0]), order[2], order[3], order[4]) for order in orders]


def get_delivered_orders_with_stores():
    orders = get_delivered_orders()
    return [(order[0], order[1], get_stores_from_order(order[0]), order[2], order[3], order[4]) for order in orders]


def get_cancelled_orders_with_stores():
    orders = get_cancelled_orders()
    return [(order[0], order[1], get_stores_from_order(order[0]), order[2], order[3], order[4]) for order in orders]


if __name__ == "__main__":
    root = create_app_root()
    configure_admin_window(root, initial_load=True)
    root.mainloop()
