# RegistrationAndLoginWindows.py - современный экран входа/регистрации
from tkinter import messagebox, Canvas, Frame, Label, Entry, Button
from app.auth.users import UserManager
from PIL import Image, ImageTk
from tkinter import ttk
import re
from app.ui.client_window import configure_client_window
from app.ui.admin_window import configure_admin_window
from app.ui.courier_window import configure_courier_window
from app.ui.theme import (
    create_app_root,
    create_app_toplevel,
    BG,
    SURFACE,
    INK,
    MUTED,
    LINE,
    ACCENT,
    ACCENT_HOVER,
    WHITE,
    FONT_TITLE,
    FONT_BODY,
    FONT_BTN,
    FONT_LABEL,
    FONT_MUTED,
    make_icon,
)

user_manager = UserManager()


def _paint_soft_bg(canvas, w, h):
    # лавандовый градиент в тон главному экрану
    for i in range(max(h, 1)):
        t = i / max(h, 1)
        r = int(0xF0 + (0xF8 - 0xF0) * t)
        g = int(0xE0 + (0xF0 - 0xE0) * t)
        b = int(0xF0 + (0xF8 - 0xF0) * t)
        canvas.create_line(0, i, w, i, fill=f"#{r:02x}{g:02x}{b:02x}")


def _field(parent, label_text, icon_kind, show=None):
    wrap = Frame(parent, bg=SURFACE)
    wrap.pack(fill="x", padx=32, pady=(10, 0))
    Label(wrap, text=label_text, bg=SURFACE, fg=MUTED, font=FONT_LABEL, anchor="w").pack(fill="x")

    row = Frame(wrap, bg=BG, highlightbackground=LINE, highlightthickness=1, bd=0)
    row.pack(fill="x", pady=(6, 0), ipady=8)

    icon = make_icon(icon_kind, color=MUTED)
    icon_lbl = Label(row, image=icon, bg=BG)
    icon_lbl.image = icon
    icon_lbl.pack(side="left", padx=(12, 6))

    entry = Entry(
        row,
        show=show,
        bg=BG,
        fg=INK,
        insertbackground=INK,
        relief="flat",
        font=FONT_BODY,
        highlightthickness=0,
    )
    entry.pack(side="left", fill="x", expand=True, padx=(0, 12), ipady=2)
    return entry


def _btn(parent, text, command, primary=True):
    from app.ui.theme import soft_button

    return soft_button(parent, text, command, primary=primary, fill="x", padx=32, pady=(14, 0))


def show_error(label, message):
    label.config(text=message)
    label.pack(fill="x", padx=32, pady=(10, 0))


def hide_error(label):
    label.pack_forget()


def validate_username(username):
    return bool(username and re.fullmatch(r"[A-Za-zА-Яа-яЁё\s\-]+", username.strip()))


def validate_phone(phone):
    return bool(re.fullmatch(r"\+7\d{10}", phone))


def validate_email(email):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email))


def _setup_auth_window(window, title, size="420x640"):
    window.title(title)
    window.geometry(size)
    window.resizable(False, False)
    window.configure(bg=BG)
    try:
        icon = ImageTk.PhotoImage(Image.open("assets/icon.png").resize((32, 32)))
        window.iconphoto(False, icon)
        window._icon = icon
    except (FileNotFoundError, OSError) as e:
        print(f"Error loading icon: {e}")

    canvas = Canvas(window, highlightthickness=0, bd=0)
    canvas.pack(fill="both", expand=True)
    w, h = int(size.split("x")[0]), int(size.split("x")[1])
    _paint_soft_bg(canvas, w, h)

    # карточка по центру
    card_w, card_h = w - 40, h - 40
    form = Frame(canvas, bg=SURFACE, highlightbackground=LINE, highlightthickness=1)
    canvas.create_window(w // 2, h // 2, anchor="center", window=form, width=card_w, height=card_h)
    return form


def open_registration_window(root):
    registration_window = create_app_toplevel(root)
    form = _setup_auth_window(registration_window, "Регистрация - GoGet", "420x720")

    Label(form, text="Создать аккаунт", bg=SURFACE, fg=INK, font=FONT_TITLE).pack(pady=(28, 4), padx=32, anchor="w")
    Label(form, text="Заполните данные - и можно заказывать", bg=SURFACE, fg=MUTED, font=FONT_MUTED).pack(
        padx=32, anchor="w"
    )

    fio_entry = _field(form, "ФИО", "user")
    email_entry = _field(form, "Email", "mail")
    phone_entry = _field(form, "Телефон (+7…)", "phone")
    password_entry = _field(form, "Пароль", "key", show="*")
    password_confirm_entry = _field(form, "Повторите пароль", "key", show="*")

    error_label = Label(form, text="", bg=SURFACE, fg="#DC2626", font=FONT_MUTED, justify="left", wraplength=320)

    def register():
        username = fio_entry.get().strip()
        phone = phone_entry.get().strip()
        email = email_entry.get().strip()
        password = password_entry.get()
        password_confirm = password_confirm_entry.get()

        errors = []
        if not validate_username(username):
            errors.append("Укажите корректное ФИО.")
        if not password or password != password_confirm:
            errors.append("Пароли не совпадают или пустые.")
        if not validate_phone(phone):
            errors.append("Телефон в формате +7XXXXXXXXXX.")
        if not validate_email(email):
            errors.append("Некорректный email.")

        if errors:
            show_error(error_label, "\n".join(errors))
            return

        hide_error(error_label)
        try:
            user_manager.register_user(username, password, email, phone)
            messagebox.showinfo("Готово", "Аккаунт создан. Теперь войдите.")
            registration_window.destroy()
            open_login_window(root)
        except Exception as e:
            show_error(error_label, f"Ошибка регистрации: {e}")

    _btn(form, "Зарегистрироваться", register, primary=True)
    _btn(form, "У меня уже есть аккаунт", lambda: (registration_window.destroy(), open_login_window(root)), primary=False)
    registration_window.grab_set()


def open_login_window(root):
    login_window = create_app_toplevel(root)
    form = _setup_auth_window(login_window, "Вход - GoGet", "420x560")

    Label(form, text="С возвращением", bg=SURFACE, fg=INK, font=FONT_TITLE).pack(pady=(36, 4), padx=32, anchor="w")
    Label(form, text="Войдите по телефону или email", bg=SURFACE, fg=MUTED, font=FONT_MUTED).pack(padx=32, anchor="w")

    username_entry = _field(form, "Телефон или email", "phone")
    password_entry = _field(form, "Пароль", "key", show="*")

    error_label = Label(form, text="", bg=SURFACE, fg="#DC2626", font=FONT_MUTED, justify="left", wraplength=320)

    def login():
        username = username_entry.get().strip()
        password = password_entry.get()

        if not username or not password:
            show_error(error_label, "Заполните все поля")
            return

        hide_error(error_label)
        try:
            role = user_manager.login_user(username, password)
            if role:
                if role == "клиент":
                    configure_client_window(root)
                elif role == "модератор":
                    configure_admin_window(root, initial_load=True)
                elif role == "курьер":
                    configure_courier_window(root)
                login_window.destroy()
            else:
                show_error(error_label, "Неверный логин или пароль.")
        except Exception as e:
            if login_window.winfo_exists():
                show_error(error_label, f"Ошибка входа: {e}")
            else:
                messagebox.showerror("Ошибка", f"Ошибка входа: {e}")

    _btn(form, "Войти", login, primary=True)
    _btn(form, "Создать аккаунт", lambda: (login_window.destroy(), open_registration_window(root)), primary=False)
    login_window.grab_set()
