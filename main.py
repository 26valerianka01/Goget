# main.py - точка входа GoGet
import tkinter as tk

from PIL import Image, ImageTk

from app.auth.users import UserManager
from app.logging_setup import setup_logging
from app.paths import asset
from app.ui.auth_windows import open_login_window, open_registration_window
from app.ui.theme import BG, HEADER, INK, MUTED, WHITE, create_app_root, soft_button

logger = setup_logging()


def create_window(image_path, width, height, icon_path):
    global root, photo, icon_photo
    root = create_app_root("GoGet - доставка", f"{width}x{height}")
    root.resizable(False, False)

    global user_manager
    user_manager = UserManager()
    try:
        user_manager.create_database()
    except Exception:
        logger.exception("Startup DB check failed")

    try:
        img = Image.open(image_path).resize((width, height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        bg = tk.Label(root, image=photo)
        bg.image = photo
        bg.place(x=0, y=0, relwidth=1, relheight=1)
    except FileNotFoundError:
        root.configure(bg=BG)

    try:
        icon_img = Image.open(icon_path)
        icon_photo = ImageTk.PhotoImage(icon_img)
        root.iconphoto(False, icon_photo)
    except FileNotFoundError:
        pass

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

    soft_button(actions, "Войти", lambda: open_login_window(root), primary=True, side="left", padx=(0, 12))
    soft_button(
        actions,
        "Регистрация",
        lambda: open_registration_window(root),
        primary=False,
        side="left",
    )

    root.mainloop()


if __name__ == "__main__":
    create_window(asset("GlavnoeOkno1.png"), 1600, 960, asset("icon.png"))
