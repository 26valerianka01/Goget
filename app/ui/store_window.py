# store_window.py
import tkinter as tk
from app.db.catalog import get_connection
from mysql.connector import Error
from tkinter import ttk
from tkinter import messagebox, Toplevel, StringVar, simpledialog
from PIL import Image, ImageTk
import re
from app.ui.theme import themed_card, pink_button, LAVENDER_BG, WHITE, TEXT_DARK, ACCENT_PINK
from tkinter.constants import BOTH, CENTER, LEFT, TOP, X, RIGHT

def load_stores(tree, search_query=None):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        if search_query:
            cursor.execute("SELECT id_магазин, название_магазин, адрес_магазин, номер_тел_магазин, эл_почта_магазин FROM Магазин WHERE название_магазин LIKE %s", ('%' + search_query + '%',))
        else:
            cursor.execute("SELECT id_магазин, название_магазин, адрес_магазин, номер_тел_магазин, эл_почта_магазин FROM Магазин")
        stores = cursor.fetchall()

        for store in stores:
            tree.insert("", "end", values=store)
    except Error as e:
        print(f"Ошибка при загрузке магазинов: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def add_store(tree):
    def save_store():
        name = name_entry.get()
        address = address_entry.get()
        phone = phone_entry.get()
        email = email_entry.get()

        errors = []
        if not validate_phone(phone):
            errors.append("Некорректный номер телефона.")

        if errors:
            messagebox.showwarning("Ошибка", "\n".join(errors))
            return

        if name and address and phone and email:
            connection = get_connection()
            try:
                cursor = connection.cursor()
                cursor.execute("INSERT INTO Магазин (название_магазин, адрес_магазин, номер_тел_магазин, эл_почта_магазин) VALUES (%s, %s, %s, %s)",
                               (name, address, phone, email))
                connection.commit()
                store_id = cursor.lastrowid
                tree.insert("", "end", values=(store_id, name, address, phone, email))
                messagebox.showinfo("Успех", "Магазин успешно добавлен!")
                add_window.destroy()
            except Error as e:
                messagebox.showerror("Ошибка", f"Ошибка при добавлении магазина: {e}")
            finally:
                if connection.is_connected():
                    cursor.close()
                    connection.close()
        else:
            messagebox.showwarning("Предупреждение", "Все поля должны быть заполнены!")

    add_window = Toplevel()
    add_window.title("GoGet")
    add_window.geometry("600x450")
    add_window.resizable(False, False)
    add_window.grab_set()

    # Добавление иконки
    try:
        icon = ImageTk.PhotoImage(Image.open("assets/icon.png").resize((32, 32)))
        add_window.iconphoto(False, icon)
    except (FileNotFoundError, IOError) as e:
        print(f"Ошибка загрузки иконки: {e}")

    main_frame = ttk.Frame(add_window)
    main_frame.pack(expand=True, fill=BOTH, padx=20, pady=20)

    title_label = ttk.Label(main_frame, text="НОВЫЙ МАГАЗИН", font=("Arial", 16))
    title_label.pack(pady=20)

    form_frame = ttk.Frame(main_frame)
    form_frame.pack(expand=True, fill=BOTH)

    # Центрирование полей ввода
    for i in range(4):
        label_frame = ttk.Frame(form_frame)
        label_frame.grid(row=i, column=0, pady=10)
        ttk.Label(label_frame, text=["Название магазина:", "Адрес:", "Номер телефона:", "Email:"][i], font=("Arial", 12)).pack(side=LEFT, padx=10)

        entry_frame = ttk.Frame(form_frame)
        entry_frame.grid(row=i, column=1, pady=10)
        if i == 0:
            name_entry = ttk.Entry(entry_frame, width=30, font=("Arial", 12))
            name_entry.pack(side=LEFT, padx=10)
        elif i == 1:
            address_entry = ttk.Entry(entry_frame, width=30, font=("Arial", 12))
            address_entry.pack(side=LEFT, padx=10)
        elif i == 2:
            phone_entry = ttk.Entry(entry_frame, width=30, font=("Arial", 12))
            phone_entry.pack(side=LEFT, padx=10)
        elif i == 3:
            email_entry = ttk.Entry(entry_frame, width=30, font=("Arial", 12))
            email_entry.pack(side=LEFT, padx=10)

    save_button = ttk.Button(form_frame, text="Добавить", command=save_store)
    save_button.grid(row=4, column=0, columnspan=2, pady=20)

def validate_phone(phone):
    return bool(re.fullmatch(r"\+7\d{10}", phone))

def update_store_info(tree, store_id, column, new_value):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(f"UPDATE Магазин SET {column} = %s WHERE id_магазин = %s", (new_value, store_id))
        connection.commit()
        messagebox.showinfo("Успех", f"Информация магазина успешно изменена!")
    except Error as e:
        messagebox.showerror("Ошибка", f"Ошибка при изменении информации магазина: {e}")
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
    store_id = tree.item(selected_item[0], "values")[0]

    if column_name == "#0":
        return

    current_value = tree.item(selected_item[0], "values")[column_number]
    new_value = simpledialog.askstring("Изменение информации", f"Введите новое значение для {column_name}:", initialvalue=current_value)

    if new_value:
        update_store_info(tree, store_id, column_name, new_value)
        tree.item(selected_item, values=(store_id, tree.item(selected_item, "values")[1], tree.item(selected_item, "values")[2], tree.item(selected_item, "values")[3], tree.item(selected_item, "values")[4], new_value))

def configure_stores_window(content_frame):
    clear_content_frame(content_frame)
    try:
        content_frame.configure(bg=LAVENDER_BG)
    except Exception:
        pass

    main_frame = tk.Frame(content_frame, bg=LAVENDER_BG)
    main_frame.pack(fill="both", expand=True, padx=60, pady=16)

    card = themed_card(main_frame)
    card.pack(fill="both", expand=True)

    tk.Label(card, text="Список магазинов", bg=WHITE, fg=TEXT_DARK, font=("Segoe UI", 16, "bold")).pack(
        anchor="w", padx=20, pady=(16, 8)
    )

    search_frame = tk.Frame(card, bg=WHITE)
    search_frame.pack(side=TOP, fill=X, padx=16, pady=8)
    tk.Label(search_frame, text="Поиск по названию магазина:", bg=WHITE, font=("Segoe UI", 12)).pack(side=LEFT)
    search_entry = ttk.Entry(search_frame, width=80, font=("Segoe UI", 12))
    search_entry.pack(side=LEFT, padx=10)

    def perform_search():
        stores_tree.delete(*stores_tree.get_children())
        load_stores(stores_tree, search_entry.get())

    tk.Button(
        search_frame,
        text="Поиск",
        command=perform_search,
        bg=ACCENT_PINK,
        fg=WHITE,
        relief="flat",
        cursor="hand2",
        font=("Segoe UI", 11, "bold"),
    ).pack(side=RIGHT)

    columns = ["ID", "Название магазина", "Адрес", "Номер телефона", "Эл. почта"]
    stores_tree = ttk.Treeview(card, columns=columns, show="headings", height=15)
    total_width = 1480
    column_width = total_width // len(columns)
    for col in columns:
        stores_tree.heading(col, text=col)
        stores_tree.column(col, width=column_width, anchor=CENTER, stretch=True)
    stores_tree.pack(fill=BOTH, expand=True, padx=16, pady=8)

    def on_mouse_wheel(event):
        try:
            if stores_tree.winfo_exists():
                stores_tree.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    stores_tree.bind("<MouseWheel>", on_mouse_wheel)
    load_stores(stores_tree)
    pink_button(main_frame, "Добавить магазин", lambda: add_store(stores_tree), fill=True, pady=10)
    stores_tree.bind("<Button-1>", lambda event: on_tree_select(event, stores_tree))

def clear_content_frame(content_frame):
    for widget in content_frame.winfo_children():
        widget.destroy()
