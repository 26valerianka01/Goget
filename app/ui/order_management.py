# order_management.py
from app.db.catalog import get_connection
from mysql.connector import Error
from tkinter import messagebox

def load_orders(orders_tree):
    if not orders_tree.winfo_exists():
        return

    # Подключение к базе данных
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id_заказы, датат_заказ, время_доставка, статус_заказ, действие_модератор
            FROM Заказы
            ORDER BY датат_заказ DESC
            LIMIT 20
        """)
        orders = cursor.fetchall()

        # Очистка Treeview
        for item in orders_tree.get_children():
            orders_tree.delete(item)

        # Вставка данных в Treeview
        for order in orders:
            orders_tree.insert("", "end", values=order)
    except Error as e:
        messagebox.showerror("Ошибка", f"Ошибка при загрузке заказов: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def load_new_orders(orders_tree):
    if not orders_tree.winfo_exists():
        return

    # Подключение к базе данных
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id_заказы, датат_заказ, время_доставка, статус_заказ, действие_модератор
            FROM Заказы
            WHERE статус_заказ = 'новый'
            ORDER BY датат_заказ DESC
        """)
        orders = cursor.fetchall()

        # Очистка Treeview
        for item in orders_tree.get_children():
            orders_tree.delete(item)

        # Вставка данных в Treeview
        for order in orders:
            orders_tree.insert("", "end", values=order)
    except Error as e:
        messagebox.showerror("Ошибка", f"Ошибка при загрузке заказов: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def update_order_status(order_id, action, user_manager, orders_tree):
    # Подключение к базе данных
    connection = get_connection()
    try:
        cursor = connection.cursor()
        if action == 'утвердить':
            new_status = 'в_процессе'
        elif action in ['отклонить', 'отменить']:
            new_status = 'отклонен'
        else:
            return

        cursor.execute("""
            UPDATE Заказы
            SET статус_заказ = %s, действие_модератор = %s, id_модератор = %s
            WHERE id_заказы = %s
        """, (new_status, action, user_manager.get_current_user_id(), order_id))
        connection.commit()
        load_orders(orders_tree)  # Обновление таблицы
    except Error as e:
        messagebox.showerror("Ошибка", f"Ошибка при обновлении статуса заказа: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def on_select(event, orders_tree, action_var, user_manager):
    selected_items = orders_tree.selection()
    if selected_items:
        selected_item = selected_items[0]
        order_id = orders_tree.item(selected_item, "values")[0]
        update_order_status(order_id, action_var.get(), user_manager, orders_tree)