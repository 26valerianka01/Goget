# checkout_button.py
from app.ui.theme import soft_button
from app.ui.order_window import create_order_window


def create_checkout_button(content_frame):
    soft_button(
        content_frame,
        "Оформить заказ",
        lambda: create_order_window(content_frame),
        primary=True,
        fill="x",
        padx=8,
        pady=24,
    )
