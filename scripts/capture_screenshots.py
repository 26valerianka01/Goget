"""Снимает скриншоты UI для README.

  python scripts/capture_screenshots.py           # все экраны
  python scripts/capture_screenshots.py client    # один экран
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

SCENES = ("home", "login", "client", "admin", "courier")


def grab(win, name: str) -> Path:
    win.update_idletasks()
    win.deiconify()
    win.lift()
    try:
        win.attributes("-topmost", True)
    except Exception:
        pass
    win.update()
    time.sleep(0.45)
    win.update()
    x, y = win.winfo_rootx(), win.winfo_rooty()
    w, h = win.winfo_width(), win.winfo_height()
    from PIL import ImageGrab

    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    path = OUT / name
    img.save(path, "PNG", optimize=True)
    print(f"saved {path.name} {img.size}")
    try:
        win.attributes("-topmost", False)
    except Exception:
        pass
    return path


def reset_user(email: str, password: str):
    """Логин без сброса singleton - иначе окна держат старый UserManager."""
    from app.auth.users import UserManager

    um = UserManager()
    um.current_user_id = None
    role = um.login_user(email, password)
    if not role:
        raise RuntimeError(f"login failed for {email}")
    print(f"login {email} -> {role} id={um.get_current_user_id()}")
    return um


def new_root(title: str = "GoGet"):
    from PIL import Image, ImageTk
    from app.paths import asset
    from app.ui.theme import create_app_root, soft_button

    root = create_app_root(title, "1600x960+40+40")
    root.resizable(False, False)
    try:
        icon = ImageTk.PhotoImage(Image.open(asset("icon.png")))
        root.iconphoto(False, icon)
        root._icon = icon
    except Exception:
        pass
    return root


def build_home(root):
    import tkinter as tk
    from PIL import Image, ImageTk
    from app.paths import asset
    from app.ui.theme import BG, HEADER, INK, MUTED, WHITE, soft_button

    for w in root.winfo_children():
        w.destroy()
    try:
        img = Image.open(asset("GlavnoeOkno1.png")).resize((1600, 960), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        bg = tk.Label(root, image=photo)
        bg.image = photo
        bg.place(x=0, y=0, relwidth=1, relheight=1)
        root._bg = photo
    except FileNotFoundError:
        root.configure(bg=BG)

    panel = tk.Frame(root, bg=WHITE, highlightthickness=0)
    panel.place(x=48, y=220, width=520, height=420)
    tk.Label(panel, text="GoGet", bg=WHITE, fg=HEADER, font=("Segoe UI Semibold", 36)).pack(
        anchor="w", padx=28, pady=(28, 0)
    )
    tk.Label(
        panel,
        text="Доставка товаров\nв пару кликов",
        bg=WHITE,
        fg=INK,
        font=("Segoe UI Semibold", 26),
        justify="left",
    ).pack(anchor="w", padx=28, pady=(12, 0))
    tk.Label(
        panel,
        text="Каталог магазинов, корзина, трекинг заказа\nи роли клиента, курьера и модератора.",
        bg=WHITE,
        fg=MUTED,
        font=("Segoe UI", 12),
        justify="left",
    ).pack(anchor="w", padx=28, pady=(16, 0))
    actions = tk.Frame(panel, bg=WHITE)
    actions.pack(anchor="w", padx=28, pady=(36, 0))
    soft_button(actions, "Войти", lambda: None, primary=True, side="left", padx=(0, 12))
    soft_button(actions, "Регистрация", lambda: None, primary=False, side="left")


def scene_home():
    root = new_root("GoGet - доставка")
    build_home(root)
    grab(root, "01-home.png")


def scene_login():
    import tkinter as tk
    from app.ui.auth_windows import open_login_window

    root = new_root("GoGet - доставка")
    build_home(root)
    open_login_window(root)
    root.update()
    time.sleep(0.35)
    tops = [w for w in root.winfo_children() if isinstance(w, tk.Toplevel)]
    grab(tops[-1] if tops else root, "02-login.png")


def scene_client():
    from app.db.catalog import get_products_by_category
    from app.services.cart import cart_items
    from app.ui.client_window import configure_client_window, render_catalog_home
    from app.ui.product_display import display_cart, on_category_click

    cart_items.clear()
    reset_user("client@example.com", "6")
    root = new_root()
    configure_client_window(root)
    grab(root, "03-client-catalog.png")

    frames = [w for w in root.pack_slaves() if w.winfo_class() in ("Frame", "TFrame") or True]
    content = None
    for w in root.pack_slaves():
        content = w  # последний pack - content_frame
    if content is not None:
        on_category_click(
            "Косметика",
            content,
            content,
            lambda: render_catalog_home(content, lambda: None),
        )
        root.update()
        # дождаться after(200) пересчёта ширины сетки товаров
        time.sleep(0.45)
        root.update()
        time.sleep(0.35)
        grab(root, "04-client-products.png")

        prods = get_products_by_category("Косметика")
        if prods:
            cart_items.append({"product": prods[0], "quantity": 2})
        for w in content.winfo_children():
            w.destroy()
        display_cart(content)
        root.update()
        time.sleep(0.35)
        grab(root, "05-client-cart.png")


def scene_admin():
    from app.ui.admin_window import configure_admin_window
    from app.ui.item_window import configure_items_window
    from app.ui.user_window import configure_users_window

    reset_user("user4@example.com", "4")
    root = new_root()
    configure_admin_window(root, initial_load=True)
    root.update()
    time.sleep(0.55)
    grab(root, "06-admin-orders.png")

    content = None
    for w in root.pack_slaves():
        content = w
    if content is not None:
        for w in content.winfo_children():
            w.destroy()
        configure_users_window(content)
        root.update()
        time.sleep(0.45)
        grab(root, "07-admin-users.png")

        for w in content.winfo_children():
            w.destroy()
        configure_items_window(content)
        root.update()
        time.sleep(0.55)
        grab(root, "08-admin-items.png")


def scene_courier():
    from app.ui.courier_window import configure_courier_window

    reset_user("user1@example.com", "password1")
    root = new_root()
    configure_courier_window(root)
    root.update()
    time.sleep(0.55)
    grab(root, "09-courier-orders.png")


HANDLERS = {
    "home": scene_home,
    "login": scene_login,
    "client": scene_client,
    "admin": scene_admin,
    "courier": scene_courier,
}


def main():
    if len(sys.argv) > 1 and sys.argv[1] in HANDLERS:
        HANDLERS[sys.argv[1]]()
        return

    # отдельный процесс на сцену - иначе ttkbootstrap падает после destroy
    for scene in SCENES:
        print(f"=== {scene} ===")
        r = subprocess.run([sys.executable, str(Path(__file__)), scene], cwd=str(ROOT))
        if r.returncode != 0:
            raise SystemExit(f"scene {scene} failed with {r.returncode}")
    print("all screenshots ok ->", OUT)


if __name__ == "__main__":
    main()
