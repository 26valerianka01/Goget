# client_window.py - клиентский UX как в современных сервисах доставки
import tkinter as tk
from tkinter import ttk
from app.db.catalog import get_categories, get_user_data
from app.ui.product_display import on_category_click, display_cart
from app.ui.order_window import update_orders_tab
from app.auth.users import UserManager
from app.services.cart import cart_items
from app.ui.theme import (
    apply_goget_styles,
    build_header,
    surface_card,
    BG,
    SURFACE,
    INK,
    MUTED,
    ACCENT,
    FONT_TITLE,
    FONT_H2,
    FONT_BODY,
    FONT_MUTED,
)

user_manager = UserManager()


def configure_client_window(root):
    root.title("GoGet - Каталог")
    root.geometry("1600x960")
    root.resizable(False, False)

    for widget in root.winfo_children():
        widget.destroy()

    style = root.style if hasattr(root, "style") else ttk.Style()
    apply_goget_styles(style)

    content_frame = tk.Frame(root, bg=BG)

    def clear_content():
        for widget in content_frame.winfo_children():
            widget.destroy()

    def on_catalog_click():
        clear_content()
        set_active("catalog")
        render_catalog_home(content_frame, on_catalog_click)

    def on_cart_click():
        clear_content()
        set_active("cart")
        display_cart(content_frame)

    def on_orders_click():
        clear_content()
        set_active("orders")
        update_orders_tab(content_frame)

    def on_profile_click():
        clear_content()
        set_active("profile")
        display_profile(content_frame)

    cart_count = sum(i["quantity"] for i in cart_items)
    cart_label = f"Корзина ({cart_count})" if cart_count else "Корзина"

    _, set_active = build_header(
        root,
        [
            ("catalog", "Каталог", on_catalog_click),
            ("cart", cart_label, on_cart_click),
            ("orders", "Заказы", on_orders_click),
            ("profile", "Профиль", on_profile_click),
        ],
        active_key="catalog",
    )
    content_frame.pack(expand=True, fill="both")
    on_catalog_click()


_CATEGORY_META = {
    "Косметика": ("✦", "#F3E5F5"),
    "Мебель": ("▣", "#EDE7F6"),
    "Детские товары": ("◎", "#FCE4EC"),
    "Одежда": ("◈", "#F3E5F5"),
    "Электроника": ("⬡", "#E8EAF6"),
    "Игрушки": ("◇", "#FCE4EC"),
}


def render_catalog_home(content_frame, on_back):
    hero = tk.Frame(content_frame, bg=BG)
    hero.pack(fill="x", padx=48, pady=(28, 8))
    tk.Label(hero, text="Что доставить сегодня?", bg=BG, fg=INK, font=FONT_TITLE).pack(anchor="w")
    tk.Label(
        hero,
        text="Выберите категорию - товары появятся с фото, ценой и кнопкой добавления в корзину",
        bg=BG,
        fg=MUTED,
        font=FONT_MUTED,
    ).pack(anchor="w", pady=(6, 0))

    grid = tk.Frame(content_frame, bg=BG)
    grid.pack(fill="both", expand=True, padx=40, pady=16)

    categories = get_categories()
    cols = 3
    for index, category in enumerate(categories):
        mark, tint = _CATEGORY_META.get(category, ("•", SURFACE))
        card = surface_card(grid, width=420, height=150)
        card.grid(row=index // cols, column=index % cols, padx=14, pady=14, sticky="nsew")
        card.grid_propagate(False)

        accent = tk.Frame(card, bg=ACCENT, width=6)
        accent.pack(side="left", fill="y")

        inner = tk.Frame(card, bg=tint)
        inner.pack(fill="both", expand=True)
        body = tk.Frame(inner, bg=tint)
        body.pack(fill="both", expand=True, padx=22, pady=22)
        tk.Label(body, text=mark, bg=tint, fg=ACCENT, font=("Segoe UI Semibold", 22)).pack(anchor="w")
        tk.Label(body, text=category, bg=tint, fg=INK, font=FONT_H2, anchor="w").pack(anchor="w", pady=(8, 0))
        tk.Label(body, text="Смотреть товары →", bg=tint, fg=ACCENT, font=FONT_MUTED, anchor="w").pack(
            anchor="w", pady=(10, 0)
        )

        def _open(c=category):
            on_category_click(c, content_frame, grid, on_back)

        for w in (card, inner, body, accent):
            w.bind("<Button-1>", lambda e, fn=_open: fn())
        for child in body.winfo_children():
            child.bind("<Button-1>", lambda e, fn=_open: fn())

    for c in range(cols):
        grid.grid_columnconfigure(c, weight=1)
    for r in range((len(categories) + cols - 1) // cols):
        grid.grid_rowconfigure(r, weight=1)


def display_profile(content_frame):
    user_data = get_user_data(user_manager.get_current_user_id())
    wrap = tk.Frame(content_frame, bg=BG)
    wrap.pack(fill="both", expand=True)

    card = surface_card(wrap)
    card.place(relx=0.5, rely=0.5, anchor="center", width=640, height=380)

    tk.Label(card, text="Личный кабинет", bg=SURFACE, fg=INK, font=FONT_TITLE).pack(anchor="w", padx=36, pady=(32, 8))
    tk.Label(card, text="Данные аккаунта", bg=SURFACE, fg=MUTED, font=FONT_MUTED).pack(anchor="w", padx=36)

    if not user_data:
        tk.Label(card, text="Данные не найдены", bg=SURFACE, fg=MUTED, font=FONT_BODY).pack(padx=36, pady=24)
        return

    fields = [
        ("ФИО", user_data[0]),
        ("Email", user_data[2]),
        ("Телефон", user_data[3]),
        ("Роль", user_data[4]),
    ]
    for label, value in fields:
        row = tk.Frame(card, bg=SURFACE)
        row.pack(fill="x", padx=36, pady=10)
        tk.Label(row, text=label, bg=SURFACE, fg=MUTED, font=FONT_MUTED, width=12, anchor="w").pack(side="left")
        tk.Label(row, text=str(value), bg=SURFACE, fg=INK, font=FONT_BODY, anchor="w").pack(side="left")
