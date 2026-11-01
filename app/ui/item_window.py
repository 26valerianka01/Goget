# item_window.py
import tkinter as tk
from app.db.catalog import get_connection
from mysql.connector import Error
from tkinter import ttk
from tkinter import messagebox, Toplevel, StringVar, simpledialog, filedialog, END
from PIL import Image, ImageTk
import re
from app.ui.theme import themed_card, pink_button, LAVENDER_BG, WHITE, TEXT_DARK, ACCENT_PINK
from tkinter.constants import BOTH, CENTER, LEFT, END, TOP, X, RIGHT

def load_items(tree, search_query=None):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        query = """
            SELECT t.id_товары, t.название_товары, t.описание_товары, t.цена_товары, m.название_магазин, c.название_категория, t.количество_товаров, t.путь_к_изображению
            FROM Товары t
            JOIN Магазин m ON t.id_магазин = m.id_магазин
            JOIN Категория c ON t.id_категория = c.id_категория
        """
        if search_query:
            query += " WHERE t.название_товары LIKE %s"
            cursor.execute(query, ('%' + search_query + '%',))
        else:
            cursor.execute(query)
        items = cursor.fetchall()

        for item in items:
            tree.insert("", "end", values=item)
    except Error as e:
        print(f"Ошибка при загрузке товаров: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def add_item(tree):
    def save_item():
        name = name_entry.get()
        description = description_entry.get()
        price = price_entry.get()
        store = store_var.get()
        category = category_var.get()
        quantity = quantity_entry.get()
        image_path = image_path_entry.get()

        errors = []
        if not validate_price(price):
            errors.append("Некорректная цена.")
        if not validate_quantity(quantity):
            errors.append("Некорректное количество.")

        if errors:
            messagebox.showwarning("Ошибка", "\n".join(errors))
            return

        if name and description and price and store and category and quantity and image_path:
            connection = get_connection()
            try:
                cursor = connection.cursor()
                cursor.execute("INSERT INTO Товары (название_товары, описание_товары, цена_товары, id_магазин, id_категория, количество_товаров, путь_к_изображению) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                               (name, description, price, store, category, quantity, image_path))
                connection.commit()
                item_id = cursor.lastrowid

                # Вставка записи в таблицу КатегорияТовары
                cursor.execute("INSERT INTO КатегорияТовары (id_категория, id_товары) VALUES (%s, %s)", (category, item_id))
                connection.commit()

                tree.insert("", "end", values=(item_id, name, description, price, store, category, quantity, image_path))
                messagebox.showinfo("Успех", "Товар успешно добавлен!")
                add_window.destroy()
            except Error as e:
                messagebox.showerror("Ошибка", f"Ошибка при добавлении товара: {e}")
            finally:
                if connection.is_connected():
                    cursor.close()
                    connection.close()
        else:
            messagebox.showwarning("Предупреждение", "Все поля должны быть заполнены!")

    add_window = Toplevel()
    add_window.title("GoGet")
    add_window.geometry("700x600")
    add_window.resizable(False, False)
    add_window.grab_set()

    try:
        icon = ImageTk.PhotoImage(Image.open("assets/icon.png").resize((32, 32)))
        add_window.iconphoto(False, icon)
    except (FileNotFoundError, IOError) as e:
        print(f"Ошибка загрузки иконки: {e}")

    main_frame = ttk.Frame(add_window)
    main_frame.pack(expand=True, fill=BOTH, padx=20, pady=20)

    title_label = ttk.Label(main_frame, text="НОВЫЙ ТОВАР", font=("Arial", 16))
    title_label.pack(pady=20)

    form_frame = ttk.Frame(main_frame)
    form_frame.pack(expand=True, fill=BOTH)

    for i in range(7):
        label_frame = ttk.Frame(form_frame)
        label_frame.grid(row=i, column=0, pady=10)
        ttk.Label(label_frame, text=["Название товара:", "Описание товара:", "Цена товара:", "Магазин:", "Категория:", "Количество товара:", "Путь к изображению:"][i], font=("Arial", 12)).pack(side=LEFT, padx=10)

        entry_frame = ttk.Frame(form_frame)
        entry_frame.grid(row=i, column=1, pady=10)
        if i == 0:
            name_entry = ttk.Entry(entry_frame, width=30, font=("Arial", 12))
            name_entry.pack(side=LEFT, padx=10)
        elif i == 1:
            description_entry = ttk.Entry(entry_frame, width=30, font=("Arial", 12))
            description_entry.pack(side=LEFT, padx=10)
        elif i == 2:
            price_entry = ttk.Entry(entry_frame, width=30, font=("Arial", 12))
            price_entry.pack(side=LEFT, padx=10)
        elif i == 3:
            store_var = StringVar()
            store_menu = ttk.OptionMenu(entry_frame, store_var, "Выберите магазин")
            store_menu.pack(side=LEFT, padx=10)
            populate_store_menu(store_menu, store_var)
        elif i == 4:
            category_var = StringVar()
            category_menu = ttk.OptionMenu(entry_frame, category_var, "Выберите категорию")
            category_menu.pack(side=LEFT, padx=10)
            populate_category_menu(category_menu, category_var)
        elif i == 5:
            quantity_entry = ttk.Entry(entry_frame, width=30, font=("Arial", 12))
            quantity_entry.pack(side=LEFT, padx=10)
        elif i == 6:
            image_path_entry = ttk.Entry(entry_frame, width=30, font=("Arial", 12))
            image_path_entry.pack(side=LEFT, padx=10)
            browse_button = ttk.Button(entry_frame, text="Обзор", command=browse_image)
            browse_button.pack(side=LEFT, padx=10)

    save_button = ttk.Button(form_frame, text="Добавить", command=save_item)
    save_button.grid(row=7, column=0, columnspan=2, pady=20)


def validate_price(price):
    return bool(re.fullmatch(r"\d+(\.\d{1,2})?", price))

def validate_quantity(quantity):
    return bool(re.fullmatch(r"\d+", quantity))

def populate_store_menu(store_menu, store_var):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id_магазин, название_магазин FROM Магазин")
        stores = cursor.fetchall()
        store_menu["menu"].delete(0, "end")
        for store in stores:
            store_menu["menu"].add_command(label=store[1], command=lambda s=store[0]: store_var.set(s))
    except Error as e:
        print(f"Ошибка при загрузке магазинов: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def populate_category_menu(category_menu, category_var):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id_категория, название_категория FROM Категория")
        categories = cursor.fetchall()
        category_menu["menu"].delete(0, "end")
        for category in categories:
            category_menu["menu"].add_command(label=category[1], command=lambda c=category[0]: category_var.set(c))
    except Error as e:
        print(f"Ошибка при загрузке категорий: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def browse_image():
    file_path = filedialog.askopenfilename(title="Выберите изображение", filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")])
    if file_path:
        image_path_entry.delete(0, END)
        image_path_entry.insert(0, file_path)

def update_item_info(tree, item_id, column, new_value):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(f"UPDATE Товары SET {column} = %s WHERE id_товары = %s", (new_value, item_id))
        connection.commit()
        messagebox.showinfo("Успех", f"Информация товара успешно изменена!")
    except Error as e:
        messagebox.showerror("Ошибка", f"Ошибка при изменении информации товара: {e}")
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
    item_id = tree.item(selected_item[0], "values")[0]

    if column_name == "#0":
        return

    current_value = tree.item(selected_item[0], "values")[column_number]
    new_value = simpledialog.askstring("Изменение информации", f"Введите новое значение для {column_name}:", initialvalue=current_value)

    if new_value:
        update_item_info(tree, item_id, column_name, new_value)
        tree.item(selected_item, values=(item_id, tree.item(selected_item, "values")[1], tree.item(selected_item, "values")[2], tree.item(selected_item, "values")[3], tree.item(selected_item, "values")[4], tree.item(selected_item, "values")[5], tree.item(selected_item, "values")[6], tree.item(selected_item, "values")[7], new_value))

def configure_items_window(content_frame):
    clear_content_frame(content_frame)
    try:
        content_frame.configure(bg=LAVENDER_BG)
    except Exception:
        pass

    main_frame = tk.Frame(content_frame, bg=LAVENDER_BG)
    main_frame.pack(fill="both", expand=True, padx=60, pady=16)

    card = themed_card(main_frame)
    card.pack(fill="both", expand=True)

    tk.Label(card, text="Список товаров", bg=WHITE, fg=TEXT_DARK, font=("Segoe UI", 16, "bold")).pack(
        anchor="w", padx=20, pady=(16, 8)
    )

    search_frame = tk.Frame(card, bg=WHITE)
    search_frame.pack(side=TOP, fill=X, padx=16, pady=8)
    tk.Label(search_frame, text="Поиск по названию товара:", bg=WHITE, font=("Segoe UI", 12)).pack(side=LEFT)
    search_entry = ttk.Entry(search_frame, width=80, font=("Segoe UI", 12))
    search_entry.pack(side=LEFT, padx=10)

    def perform_search():
        items_tree.delete(*items_tree.get_children())
        load_items(items_tree, search_entry.get())

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

    columns = [
        "ID",
        "Название товара",
        "Описание товара",
        "Цена товара",
        "Магазин",
        "Категория",
        "Количество товара",
        "Путь к изображению",
    ]
    items_tree = ttk.Treeview(card, columns=columns, show="headings", height=15)
    total_width = 1480
    column_width = total_width // len(columns)
    for col in columns:
        items_tree.heading(col, text=col)
        items_tree.column(col, width=column_width, anchor=CENTER, stretch=True)
    items_tree.pack(fill=BOTH, expand=True, padx=16, pady=8)

    def on_mouse_wheel(event):
        try:
            if items_tree.winfo_exists():
                items_tree.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    items_tree.bind("<MouseWheel>", on_mouse_wheel)
    load_items(items_tree)

    actions = tk.Frame(main_frame, bg=LAVENDER_BG)
    actions.pack(fill="x", pady=10)
    left = tk.Frame(actions, bg=LAVENDER_BG)
    right = tk.Frame(actions, bg=LAVENDER_BG)
    left.pack(side="left", fill="x", expand=True, padx=(0, 6))
    right.pack(side="left", fill="x", expand=True, padx=(6, 0))
    pink_button(left, "Добавить категорию", add_category, fill=True)
    pink_button(right, "Добавить товар", lambda: add_item(items_tree), fill=True)
    items_tree.bind("<Button-1>", lambda event: on_tree_select(event, items_tree))

def add_category():
    def save_category():
        name = name_entry.get()
        if name:
            connection = get_connection()
            try:
                cursor = connection.cursor()
                cursor.execute("INSERT INTO Категория (название_категория) VALUES (%s)", (name,))
                connection.commit()
                messagebox.showinfo("Успех", "Категория успешно добавлена!")
                add_window.destroy()
            except Error as e:
                messagebox.showerror("Ошибка", f"Ошибка при добавлении категории: {e}")
            finally:
                if connection.is_connected():
                    cursor.close()
                    connection.close()
        else:
            messagebox.showwarning("Предупреждение", "Поле должно быть заполнено!")

    add_window = Toplevel()
    add_window.title("GoGet")
    add_window.geometry("500x250")
    add_window.resizable(False, False)
    add_window.grab_set()

    try:
        icon = ImageTk.PhotoImage(Image.open("assets/icon.png").resize((32, 32)))
        add_window.iconphoto(False, icon)
    except (FileNotFoundError, IOError) as e:
        print(f"Ошибка загрузки иконки: {e}")

    main_frame = ttk.Frame(add_window)
    main_frame.pack(expand=True, fill=BOTH, padx=20, pady=20)

    title_label = ttk.Label(main_frame, text="НОВАЯ КАТЕГОРИЯ", font=("Arial", 16))
    title_label.pack(pady=20)

    form_frame = ttk.Frame(main_frame)
    form_frame.pack(expand=True, fill=BOTH)

    label_frame = ttk.Frame(form_frame)
    label_frame.grid(row=0, column=0, pady=10)
    ttk.Label(label_frame, text="Название категории:", font=("Arial", 12)).pack(side=LEFT, padx=10)

    entry_frame = ttk.Frame(form_frame)
    entry_frame.grid(row=0, column=1, pady=10)
    name_entry = ttk.Entry(entry_frame, width=20, font=("Arial", 12))
    name_entry.pack(side=LEFT, padx=10)

    save_button = ttk.Button(form_frame, text="Добавить", command=save_category)
    save_button.grid(row=1, column=0, columnspan=2, pady=20)

def clear_content_frame(content_frame):
    for widget in content_frame.winfo_children():
        widget.destroy()
