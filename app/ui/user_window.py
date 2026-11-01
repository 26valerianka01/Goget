# user_window.py
import tkinter as tk
from app.db.catalog import get_connection
from mysql.connector import Error
from tkinter import ttk
from tkinter import messagebox, Toplevel, StringVar, simpledialog
from PIL import Image, ImageTk
import re
from app.auth.passwords import hash_password
from app.paths import asset
from app.ui.theme import themed_card, pink_button, LAVENDER_BG, WHITE, TEXT_DARK, create_app_root
from tkinter.constants import BOTH, CENTER, LEFT

PASSWORD_MASK = "••••••"


def load_users(tree, role=None):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        if role:
            cursor.execute(
                "SELECT id_пользователя, ФИО, эл_почта, номер_телефона, роль FROM Пользователи WHERE роль = %s",
                (role,),
            )
        else:
            cursor.execute(
                "SELECT id_пользователя, ФИО, эл_почта, номер_телефона, роль FROM Пользователи"
            )
        users = cursor.fetchall()

        for user_id, fio, email, phone, user_role in users:
            tree.insert(
                "",
                "end",
                values=(user_id, fio, PASSWORD_MASK, email, phone, user_role),
            )
    except Error as e:
        print(f"Ошибка при загрузке пользователей: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def add_user(tree):
    def save_user():
        fio = fio_entry.get()
        email = email_entry.get()
        phone = phone_entry.get()
        password = password_entry.get()
        password_confirm = password_confirm_entry.get()
        role = role_var.get()

        errors = []
        if not validate_fio(fio):
            errors.append("Некорректное ФИО.")
        if not password or password != password_confirm:
            errors.append("Пароли не совпадают или пустые.")
        if not validate_phone(phone):
            errors.append("Некорректный номер телефона.")
        if not validate_email(email):
            errors.append("Некорректный email.")

        if errors:
            messagebox.showwarning("Ошибка", "\n".join(errors))
            return

        if fio and email and phone and password and role:
            connection = get_connection()
            try:
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO Пользователи (ФИО, пароль, эл_почта, номер_телефона, роль) VALUES (%s, %s, %s, %s, %s)",
                    (fio, hash_password(password), email, phone, role),
                )
                connection.commit()
                user_id = cursor.lastrowid
                tree.insert("", "end", values=(user_id, fio, PASSWORD_MASK, email, phone, role))
                messagebox.showinfo("Успех", "Пользователь успешно добавлен!")
                add_window.destroy()
            except Error as e:
                messagebox.showerror("Ошибка", f"Ошибка при добавлении пользователя: {e}")
            finally:
                if connection.is_connected():
                    cursor.close()
                    connection.close()
        else:
            messagebox.showwarning("Предупреждение", "Все поля должны быть заполнены!")

    add_window = Toplevel()
    add_window.title("GoGet")
    add_window.geometry("600x750")
    add_window.resizable(False, False)
    add_window.grab_set()

    # Добавление иконки
    try:
        icon = ImageTk.PhotoImage(Image.open(asset("icon.png")).resize((32, 32)))
        add_window.iconphoto(False, icon)
    except (FileNotFoundError, IOError) as e:
        print(f"Ошибка загрузки иконки: {e}")

    main_frame = ttk.Frame(add_window)
    main_frame.pack(expand=True, fill=BOTH, padx=20, pady=20)

    title_label = ttk.Label(main_frame, text="НОВЫЙ ПОЛЬЗОВАТЕЛЬ", font=("Arial", 16))
    title_label.pack(pady=20)

    form_frame = ttk.Frame(main_frame)
    form_frame.pack(expand=True, fill=BOTH)

    # Центрирование полей ввода
    for i in range(6):
        label_frame = ttk.Frame(form_frame)
        label_frame.grid(row=i, column=0, pady=10)
        ttk.Label(label_frame, text=["ФИО:", "Email:", "Номер телефона:", "Пароль:", "Повторите пароль:", "Роль:"][i], font=("Arial", 12)).pack(side=LEFT, padx=10)

        entry_frame = ttk.Frame(form_frame)
        entry_frame.grid(row=i, column=1, pady=10)
        if i == 0:
            fio_entry = ttk.Entry(entry_frame, width=30, font=("Arial", 12))
            fio_entry.pack(side=LEFT, padx=10)
        elif i == 1:
            email_entry = ttk.Entry(entry_frame, width=30, font=("Arial", 12))
            email_entry.pack(side=LEFT, padx=10)
        elif i == 2:
            phone_entry = ttk.Entry(entry_frame, width=30, font=("Arial", 12))
            phone_entry.pack(side=LEFT, padx=10)
        elif i == 3:
            password_entry = ttk.Entry(entry_frame, width=30, show="*", font=("Arial", 12))
            password_entry.pack(side=LEFT, padx=10)
        elif i == 4:
            password_confirm_entry = ttk.Entry(entry_frame, width=30, show="*", font=("Arial", 12))
            password_confirm_entry.pack(side=LEFT, padx=10)
        elif i == 5:
            role_var = StringVar(value="клиент")
            role_menu = ttk.OptionMenu(entry_frame, role_var, "клиент", "клиент", "модератор", "курьер")
            role_menu.pack(side=LEFT, padx=10)

    save_button = ttk.Button(form_frame, text="Добавить", command=save_user)
    save_button.grid(row=6, column=0, columnspan=2, pady=20)

def validate_fio(fio):
    return bool(re.fullmatch(r"[А-Яа-яЁё\s]+", fio))

def validate_phone(phone):
    return bool(re.fullmatch(r"\+7\d{10}", phone))

def validate_email(email):
    return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email))

_COLUMN_TO_DB = {
    "ФИО": "ФИО",
    "Пароль": "пароль",
    "Эл. почта": "эл_почта",
    "Номер телефона": "номер_телефона",
    "Роль": "роль",
}


def update_user_info(tree, user_id, column, new_value):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        if column == "Роль":
            cursor.execute(
                "UPDATE Пользователи SET роль = %s WHERE id_пользователя = %s",
                (new_value, user_id),
            )
            connection.commit()

            if new_value == "курьер":
                cursor.execute(
                    "INSERT INTO Курьер (id_курьер, статус_курьер, текущие_заказы) VALUES (%s, %s, %s)",
                    (user_id, "доступен", 0),
                )
                connection.commit()
            elif new_value != "курьер":
                cursor.execute("DELETE FROM Курьер WHERE id_курьер = %s", (user_id,))
                connection.commit()
        else:
            db_col = _COLUMN_TO_DB.get(column)
            if not db_col:
                messagebox.showwarning("Ошибка", "Это поле нельзя изменить.")
                return False
            value = hash_password(new_value) if column == "Пароль" else new_value
            cursor.execute(
                f"UPDATE Пользователи SET `{db_col}` = %s WHERE id_пользователя = %s",
                (value, user_id),
            )
            connection.commit()

        messagebox.showinfo("Успех", "Информация пользователя успешно изменена!")
        return True
    except Error as e:
        messagebox.showerror("Ошибка", f"Ошибка при изменении информации пользователя: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def on_tree_select(event, tree):
    selected_item = tree.selection()
    if not selected_item:
        return

    column = tree.identify_column(event.x)
    column_number = int(column[1:]) - 1
    column_name = tree["columns"][column_number]
    values = list(tree.item(selected_item[0], "values"))
    user_id = values[0]

    if column_name in ("#0", "ID"):
        return

    initial = "" if column_name == "Пароль" else values[column_number]
    new_value = simpledialog.askstring(
        "Изменение информации",
        f"Введите новое значение для {column_name}:",
        initialvalue=initial,
    )

    if new_value:
        if update_user_info(tree, user_id, column_name, new_value):
            values[column_number] = PASSWORD_MASK if column_name == "Пароль" else new_value
            tree.item(selected_item, values=values)

def configure_users_window(content_frame):
    clear_content_frame(content_frame)
    try:
        content_frame.configure(bg=LAVENDER_BG)
    except Exception:
        pass

    main_frame = tk.Frame(content_frame, bg=LAVENDER_BG)
    main_frame.pack(fill="both", expand=True, padx=60, pady=16)

    card = themed_card(main_frame)
    card.pack(fill="both", expand=True)

    tk.Label(card, text="Последние 20 пользователей", bg=WHITE, fg=TEXT_DARK, font=("Segoe UI", 16, "bold")).pack(
        anchor="w", padx=20, pady=(16, 8)
    )

    columns = ["ID", "ФИО", "Пароль", "Эл. почта", "Номер телефона", "Роль"]
    users_tree = ttk.Treeview(card, columns=columns, show="headings", height=15)
    total_width = 1480
    column_width = total_width // len(columns)
    for col in columns:
        users_tree.heading(col, text=col)
        users_tree.column(col, width=column_width, anchor=CENTER, stretch=True)
    users_tree.pack(fill=BOTH, expand=True, padx=16, pady=8)

    def on_mouse_wheel(event):
        try:
            if users_tree.winfo_exists():
                users_tree.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    users_tree.bind("<MouseWheel>", on_mouse_wheel)
    load_users(users_tree)
    pink_button(main_frame, "Добавить пользователя", lambda: add_user(users_tree), fill=True, pady=10)
    users_tree.bind("<Button-1>", lambda event: on_tree_select(event, users_tree))

def open_users_window():
    users_window = Toplevel()
    users_window.title("GoGet")
    users_window.geometry("1600x960")

    try:
        icon = ImageTk.PhotoImage(Image.open(asset("icon.png")).resize((32, 32)))
        users_window.iconphoto(False, icon)
    except (FileNotFoundError, IOError) as e:
        print(f"Ошибка загрузки иконки: {e}")

    content_frame = ttk.Frame(users_window)
    content_frame.pack(fill=BOTH, expand=True)

    notebook = ttk.Notebook(content_frame)
    notebook.pack(fill=BOTH, expand=True, pady=10)

    couriers_frame = ttk.Frame(notebook)
    admins_frame = ttk.Frame(notebook)
    clients_frame = ttk.Frame(notebook)

    notebook.add(couriers_frame, text="Курьеры")
    notebook.add(admins_frame, text="Модераторы")
    notebook.add(clients_frame, text="Клиенты")

    columns = ["ID", "ФИО", "Пароль", "Эл. почта", "Номер телефона", "Роль"]

    couriers_tree = ttk.Treeview(couriers_frame, columns=columns, show="headings", height=15)
    admins_tree = ttk.Treeview(admins_frame, columns=columns, show="headings", height=15)
    clients_tree = ttk.Treeview(clients_frame, columns=columns, show="headings", height=15)

    style = ttk.Style()
    style.configure("Treeview.Heading", font=("Arial", 14), background="white", foreground="black")
    style.configure("Treeview", rowheight=40)

    total_width = 1480
    column_width = total_width // len(columns)

    for col in columns:
        couriers_tree.heading(col, text=col)
        couriers_tree.column(col, width=column_width, anchor=CENTER, stretch=True)
        admins_tree.heading(col, text=col)
        admins_tree.column(col, width=column_width, anchor=CENTER, stretch=True)
        clients_tree.heading(col, text=col)
        clients_tree.column(col, width=column_width, anchor=CENTER, stretch=True)

    couriers_tree.pack(fill=BOTH, expand=True, pady=10)
    admins_tree.pack(fill=BOTH, expand=True, pady=10)
    clients_tree.pack(fill=BOTH, expand=True, pady=10)

    def on_mouse_wheel(event):
        current_tab = notebook.select()
        if current_tab == str(couriers_frame):
            couriers_tree.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif current_tab == str(admins_frame):
            admins_tree.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif current_tab == str(clients_frame):
            clients_tree.yview_scroll(int(-1 * (event.delta / 120)), "units")

    couriers_tree.bind("<MouseWheel>", on_mouse_wheel)
    admins_tree.bind("<MouseWheel>", on_mouse_wheel)
    clients_tree.bind("<MouseWheel>", on_mouse_wheel)

    load_users(couriers_tree, "курьер")
    load_users(admins_tree, "модератор")
    load_users(clients_tree, "клиент")

def clear_content_frame(content_frame):
    for widget in content_frame.winfo_children():
        widget.destroy()

# Пример использования функции open_users_window в основном окне
def main_window():
    root = create_app_root()
    root.title("Основное окно")
    root.geometry("800x600")

    content_frame = ttk.Frame(root)
    content_frame.pack(fill=BOTH, expand=True)

    configure_users_window(content_frame)

    root.mainloop()

if __name__ == "__main__":
    main_window()



