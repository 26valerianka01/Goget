# product_display.py - каталог и корзина
import tkinter as tk
from tkinter import messagebox

from pathlib import Path

from PIL import Image, ImageTk
from app.db.catalog import get_products_by_category
from app.paths import PROJECT_ROOT
from app.ui.checkout_button import create_checkout_button
from app.services.cart import cart_items
from app.ui.scroll import make_scrollable
from app.ui.theme import (
    BG,
    SURFACE,
    INK,
    MUTED,
    ACCENT,
    ACCENT_HOVER,
    LINE,
    WHITE,
    FONT_H2,
    FONT_BODY,
    FONT_PRICE,
    FONT_MUTED,
    FONT_BTN,
    soft_button,
    surface_card,
)


def _resolve_image_path(raw) -> Path:
    """Пути в БД могут быть Foto/... или assets/... - ищем от корня проекта."""
    text = str(raw).strip().strip('"').replace("\\", "/")
    candidates = [Path(text), PROJECT_ROOT / text]
    if text.startswith("Foto/"):
        candidates.append(PROJECT_ROOT / ("assets/" + text[len("Foto/") :]))
    elif text.startswith("assets/"):
        candidates.append(PROJECT_ROOT / ("Foto/" + text[len("assets/") :]))
    for path in candidates:
        if path.is_file():
            return path
    return candidates[0]


def on_category_click(category, content_frame, _categories_frame, on_back_click):
    for widget in content_frame.winfo_children():
        widget.destroy()

    top = tk.Frame(content_frame, bg=BG)
    top.pack(fill="x", padx=40, pady=(20, 0))

    back = tk.Label(top, text="← Каталог", bg=BG, fg=ACCENT, font=FONT_BTN, cursor="hand2")
    back.pack(anchor="w")
    back.bind("<Button-1>", lambda _e: on_back_click())
    back.bind("<Enter>", lambda _e: back.configure(fg=ACCENT_HOVER))
    back.bind("<Leave>", lambda _e: back.configure(fg=ACCENT))
    tk.Label(top, text=category, bg=BG, fg=INK, font=("Segoe UI Semibold", 22)).pack(anchor="w", pady=(8, 4))
    tk.Label(top, text="Добавляйте товары в корзину одним нажатием", bg=BG, fg=MUTED, font=FONT_MUTED).pack(
        anchor="w"
    )

    # симметричные поля: скроллбар уже справа у canvas
    _outer, _canvas, scrollable = make_scrollable(content_frame, bg=BG, padx=(16, 8), pady=(8, 12))

    products = get_products_by_category(category)
    if not products:
        tk.Label(scrollable, text="В этой категории пока нет товаров", bg=BG, fg=MUTED, font=FONT_BODY).pack(
            pady=48
        )
        return

    cols = 4

    def _render_grid(avail_w: int):
        for child in scrollable.winfo_children():
            child.destroy()

        # вся ширина canvas делится на 4 колонки без «хвоста» справа
        side = 4
        gap = 12
        usable = max(int(avail_w) - side * 2, 640)
        card_w = max(200, (usable - gap * cols) // cols)
        # добиваем остаток пикселей в ширину карточки, чтобы не копился зазор
        rem = usable - (card_w * cols + gap * cols)
        card_w += max(0, rem // cols)
        # слот под фото фиксированный, само фото - contain (без растягивания)
        slot_w = max(180, card_w - 28)
        slot_h = int(slot_w * 0.75)
        wrap_len = max(120, card_w - 36)

        inner = tk.Frame(scrollable, bg=BG)
        inner.pack(fill="both", expand=True, padx=side, pady=side)
        for c in range(cols):
            inner.grid_columnconfigure(c, weight=1, uniform="product", minsize=card_w)

        r = c = 0
        for product in products:
            wrap = tk.Frame(inner, bg=BG)
            wrap.grid(row=r, column=c, padx=gap // 2, pady=gap // 2, sticky="nsew")

            card = surface_card(wrap)
            card.pack(fill="both", expand=True)

            slot = tk.Frame(card, bg=SURFACE, width=slot_w, height=slot_h)
            slot.pack(pady=(10, 6), padx=10)
            slot.pack_propagate(False)
            try:
                raw = Image.open(_resolve_image_path(product[4]))
                raw.thumbnail((slot_w - 8, slot_h - 8), Image.LANCZOS)
                photo = ImageTk.PhotoImage(raw)
                img = tk.Label(slot, image=photo, bg=SURFACE, bd=0)
                img.image = photo
                img.place(relx=0.5, rely=0.5, anchor="center")
            except Exception:
                tk.Label(slot, text="Нет фото", bg=LINE, fg=MUTED, font=FONT_BODY).place(
                    relx=0.5, rely=0.5, anchor="center"
                )

            tk.Label(
                card,
                text=str(product[1]),
                bg=SURFACE,
                fg=INK,
                font=FONT_BODY,
                wraplength=wrap_len,
                justify="left",
            ).pack(anchor="w", fill="x", padx=12)
            store_name = product[6] if len(product) > 6 else "-"
            tk.Label(
                card,
                text=f"Магазин: {store_name}",
                bg=SURFACE,
                fg=MUTED,
                font=FONT_MUTED,
                wraplength=wrap_len,
                justify="left",
            ).pack(anchor="w", fill="x", padx=12, pady=(2, 0))
            tk.Label(card, text=f"{product[3]} ₽", bg=SURFACE, fg=INK, font=FONT_PRICE).pack(
                anchor="center", pady=(4, 0)
            )
            soft_button(
                card,
                "+ В корзину",
                lambda p=product: add_to_cart(p),
                primary=True,
                fill="x",
                padx=12,
                pady=(10, 12),
            )

            c += 1
            if c >= cols:
                c = 0
                r += 1

    def _relayout(_event=None):
        content_frame.update_idletasks()
        _canvas.update_idletasks()
        w = _canvas.winfo_width()
        if w < 400:
            w = max(content_frame.winfo_width() - 40, 1200)
        prev = getattr(_canvas, "_last_grid_w", 0)
        if _event is not None and abs(w - prev) < 20 and prev > 0:
            return
        _canvas._last_grid_w = w
        _render_grid(w)

    _canvas.bind("<Configure>", _relayout, add="+")
    content_frame.after_idle(_relayout)
    content_frame.after(80, _relayout)
    content_frame.after(250, _relayout)


def add_to_cart(product):
    store_id = product[5]
    if cart_items:
        if cart_items[0]["product"][5] != store_id:
            messagebox.showerror(
                "Разные магазины",
                "В одной корзине могут быть товары только из одного магазина.",
            )
            return
    for item in cart_items:
        if item["product"] == product:
            item["quantity"] += 1
            return
    cart_items.append({"product": product, "quantity": 1})


def update_cart_item(product, quantity_change, content_frame):
    for item in cart_items:
        if item["product"] == product:
            item["quantity"] += quantity_change
            if item["quantity"] <= 0:
                cart_items.remove(item)
            break
    display_cart(content_frame)


def remove_from_cart(product, content_frame):
    cart_items[:] = [i for i in cart_items if i["product"] != product]
    display_cart(content_frame)


def display_cart(content_frame):
    for widget in content_frame.winfo_children():
        widget.destroy()

    header = tk.Frame(content_frame, bg=BG)
    header.pack(fill="x", padx=48, pady=(24, 8))
    tk.Label(header, text="Корзина", bg=BG, fg=INK, font=("Segoe UI Semibold", 22)).pack(anchor="w")

    if not cart_items:
        tk.Label(content_frame, text="Пока пусто - загляните в каталог", bg=BG, fg=MUTED, font=FONT_BODY).pack(
            pady=40
        )
        return

    total = sum(i["quantity"] * float(i["product"][3]) for i in cart_items)
    tk.Label(header, text=f"Итого: {total:.2f} ₽", bg=BG, fg=MUTED, font=FONT_MUTED).pack(anchor="w", pady=(4, 0))

    _, _canvas, scrollable = make_scrollable(content_frame, bg=BG, padx=(40, 8), pady=(0, 12))

    for item in cart_items:
        product = item["product"]
        quantity = item["quantity"]
        line_sum = quantity * float(product[3])

        row = surface_card(scrollable)
        row.pack(fill="x", pady=8, padx=8)

        try:
            image = Image.open(_resolve_image_path(product[4])).resize((88, 88), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            img = tk.Label(row, image=photo, bg=SURFACE)
            img.image = photo
            img.pack(side="left", padx=16, pady=16)
        except Exception:
            tk.Label(row, text="фото", bg=LINE, fg=MUTED, width=10, height=4).pack(side="left", padx=16, pady=16)

        info = tk.Frame(row, bg=SURFACE)
        info.pack(side="left", fill="x", expand=True, pady=16)
        tk.Label(info, text=str(product[1]), bg=SURFACE, fg=INK, font=FONT_H2, anchor="w").pack(anchor="w")
        store_name = product[6] if len(product) > 6 else "-"
        tk.Label(info, text=f"Магазин: {store_name}", bg=SURFACE, fg=MUTED, font=FONT_MUTED, anchor="w").pack(
            anchor="w", pady=(2, 0)
        )
        tk.Label(info, text=f"{product[3]} ₽ / шт.", bg=SURFACE, fg=MUTED, font=FONT_MUTED, anchor="w").pack(
            anchor="w", pady=(4, 0)
        )

        qty = tk.Frame(row, bg=SURFACE)
        qty.pack(side="left", padx=12)
        for text, delta in (("−", -1), (None, 0), ("+", 1)):
            if delta == 0:
                tk.Label(qty, text=str(quantity), bg=SURFACE, fg=INK, font=FONT_PRICE, width=3).pack(side="left")
            else:
                soft_button(
                    qty,
                    text,
                    lambda p=product, d=delta: update_cart_item(p, d, content_frame),
                    primary=True,
                    side="left",
                    padx=2,
                )

        tk.Label(row, text=f"{line_sum:.2f} ₽", bg=SURFACE, fg=INK, font=FONT_PRICE).pack(side="left", padx=16)
        del_btn = tk.Label(row, text="Удалить", bg=SURFACE, fg="#DC2626", cursor="hand2", font=FONT_MUTED, padx=12)
        del_btn.pack(side="right", padx=16)
        del_btn.bind("<Button-1>", lambda _e, p=product: remove_from_cart(p, content_frame))

    create_checkout_button(scrollable)
