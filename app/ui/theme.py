# Дизайн-система GoGet - цвета с главного экрана (фиолетовый грузовик / логотип)
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw

# --- Tokens с GlavnoeOkno / icon ---
BG = "#F7F0F8"
SURFACE = "#FFFFFF"
INK = "#2A1040"
MUTED = "#7A6A8A"
LINE = "#E8D5F0"
ACCENT = "#7B1FA2"
ACCENT_HOVER = "#5E1580"
ACCENT_SOFT = "#F3E5F5"
ACCENT_MAGENTA = "#C2188A"
DANGER = "#DC2626"
SUCCESS = "#059669"
HEADER = "#300060"
WHITE = "#FFFFFF"
CREAM = "#F5E6C8"

# совместимость со старыми импортами
LAVENDER_BG = BG
PURPLE_HEADER = HEADER
PURPLE_DARK = "#2A0A4A"
PURPLE_MID = "#4A1B7A"
ACCENT_PINK = ACCENT
ACCENT_PINK_HOVER = ACCENT_HOVER
BORDER_PINK = "#D4A5E8"
TEXT_DARK = INK

FONT_DISPLAY = ("Segoe UI Semibold", 28)
FONT_TITLE = ("Segoe UI Semibold", 20)
FONT_H2 = ("Segoe UI Semibold", 16)
FONT_BODY = ("Segoe UI", 12)
FONT_LABEL = ("Segoe UI", 11)
FONT_NAV = ("Segoe UI Semibold", 13)
FONT_BTN = ("Segoe UI Semibold", 12)
FONT_PRICE = ("Segoe UI Semibold", 14)
FONT_MUTED = ("Segoe UI", 11)
FONT_CARD = FONT_BODY


def apply_goget_styles(style):
    """Стили для стандартного ttk (тема clam) - без ttkbootstrap Flatly.

    Flatly/ttkbootstrap на Windows перекрашивает tk.Label/Button в navy
    и игнорирует bg= - из‑за этого пропадал фиолетовый бренд.
    """
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(".", background=BG, foreground=INK, font=FONT_BODY)
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=INK)
    style.configure(
        "Treeview",
        background=SURFACE,
        fieldbackground=SURFACE,
        foreground=INK,
        rowheight=38,
        font=FONT_BODY,
        borderwidth=0,
        relief="flat",
    )
    style.configure(
        "Treeview.Heading",
        background=ACCENT_SOFT,
        foreground=INK,
        font=FONT_NAV,
        relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", ACCENT)],
        foreground=[("selected", WHITE)],
    )
    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure("TNotebook.Tab", font=FONT_NAV, padding=(16, 8), background=ACCENT_SOFT)
    style.map("TNotebook.Tab", background=[("selected", SURFACE)])
    style.configure(
        "TButton",
        font=FONT_BTN,
        padding=(14, 8),
        background=ACCENT,
        foreground=WHITE,
        borderwidth=0,
        focusthickness=0,
    )
    style.map(
        "TButton",
        background=[("active", ACCENT_HOVER), ("pressed", ACCENT_HOVER)],
        foreground=[("active", WHITE)],
    )
    style.configure(
        "TMenubutton",
        font=FONT_BTN,
        padding=(12, 6),
        background=ACCENT,
        foreground=WHITE,
    )
    style.map("TMenubutton", background=[("active", ACCENT_HOVER)])


def create_app_root(title: str = "GoGet", size: str = "1600x960"):
    """Корневое окно на чистом tk.Tk - цвета бренда работают на Windows."""
    root = tk.Tk()
    root.title(title)
    root.geometry(size)
    root.configure(bg=BG)
    from tkinter import ttk as _ttk

    style = _ttk.Style(root)
    apply_goget_styles(style)
    root.style = style
    return root


def create_app_toplevel(master=None, title: str = "GoGet", size: str = "420x640"):
    win = tk.Toplevel(master) if master is not None else tk.Toplevel()
    win.title(title)
    win.geometry(size)
    win.configure(bg=BG)
    return win


def soft_button(parent, text, command, primary=True, **pack_kwargs):
    """
    Кнопка через Frame+Label: на Windows tk.Button игнорирует bg (native theme).
    Frame гарантирует цветную плашку на всю ширину при fill='x'.
    """
    bg = ACCENT if primary else SURFACE
    fg = WHITE if primary else INK
    hover = ACCENT_HOVER if primary else ACCENT_SOFT

    wrap = tk.Frame(
        parent,
        bg=bg,
        highlightthickness=0 if primary else 1,
        highlightbackground=LINE,
        cursor="hand2",
    )
    btn = tk.Label(wrap, text=text, bg=bg, fg=fg, font=FONT_BTN, cursor="hand2", padx=20, pady=12)
    btn.pack()

    def _enter(_e=None):
        wrap.configure(bg=hover)
        btn.configure(bg=hover, fg=WHITE if primary else INK)

    def _leave(_e=None):
        wrap.configure(bg=bg)
        btn.configure(bg=bg, fg=fg)

    def _click(_e=None):
        if command:
            command()

    for w in (wrap, btn):
        w.bind("<Enter>", _enter)
        w.bind("<Leave>", _leave)
        w.bind("<Button-1>", _click)

    fill = pack_kwargs.pop("fill", None)
    if fill:
        wrap.pack(fill=fill, **pack_kwargs)
    else:
        wrap.pack(**pack_kwargs)
    wrap._label = btn
    return wrap


pink_button = lambda parent, text, command, fill=True, **kw: soft_button(
    parent, text, command, primary=True, fill="x" if fill else None, **kw
)


def surface_card(parent, **kwargs):
    defaults = dict(bg=SURFACE, highlightbackground=LINE, highlightthickness=1, bd=0)
    defaults.update(kwargs)
    return tk.Frame(parent, **defaults)


themed_card = surface_card


def chip(parent, text, command=None, active=False):
    bg = ACCENT if active else SURFACE
    fg = WHITE if active else INK
    hover = ACCENT_HOVER if active else ACCENT_SOFT
    btn = tk.Label(
        parent,
        text=text,
        bg=bg,
        fg=fg,
        font=FONT_NAV,
        cursor="hand2",
        padx=16,
        pady=8,
        highlightthickness=1,
        highlightbackground=ACCENT if active else LINE,
    )

    def _enter(_e=None):
        btn.configure(bg=hover)

    def _leave(_e=None):
        btn.configure(bg=bg)

    def _click(_e=None):
        if command:
            command()

    btn.bind("<Enter>", _enter)
    btn.bind("<Leave>", _leave)
    btn.bind("<Button-1>", _click)
    return btn


def build_header(root, nav_items, active_key=None):
    """Фиолетовая шапка (Canvas - цвет не съедает native theme Windows)."""
    header = tk.Canvas(root, height=72, highlightthickness=0, bd=0)
    header.pack(fill="x", side="top")

    logo_wrap = tk.Frame(header, bg=HEADER)
    logo_id = header.create_window(28, 36, anchor="w", window=logo_wrap)

    try:
        from app.paths import asset

        icon = Image.open(asset("icon.png")).resize((26, 26))
        icon_photo = ImageTk.PhotoImage(icon)
        logo_icon = tk.Label(logo_wrap, image=icon_photo, bg=HEADER)
        logo_icon.image = icon_photo
        logo_icon.pack(side="left", padx=(0, 10))
    except Exception:
        tk.Label(logo_wrap, text="◆", fg=CREAM, bg=HEADER, font=("Segoe UI", 16)).pack(side="left", padx=(0, 8))
    tk.Label(logo_wrap, text="GoGet", fg=WHITE, bg=HEADER, font=("Segoe UI Semibold", 18)).pack(side="left")
    tk.Label(logo_wrap, text="  доставка", fg="#C4A8E0", bg=HEADER, font=FONT_MUTED).pack(side="left", pady=(4, 0))

    nav = tk.Frame(header, bg=HEADER)
    nav_id = header.create_window(100, 36, anchor="e", window=nav)

    def _layout(_event=None):
        w = max(header.winfo_width(), 1)
        header.delete("bg")
        header.create_rectangle(0, 0, w, 72, fill=HEADER, outline=HEADER, tags="bg")
        header.tag_lower("bg")
        header.coords(logo_id, 28, 36)
        header.coords(nav_id, w - 28, 36)

    header.bind("<Configure>", _layout)
    header.after_idle(_layout)

    nav_labels = {}

    def set_active(name):
        for key, lbl in nav_labels.items():
            if key == name:
                lbl.config(fg="#FFB3E6", font=("Segoe UI Semibold", 13, "underline"))
            else:
                lbl.config(fg="#E8D5F0", font=FONT_NAV)

    for key, text, command in nav_items:
        lbl = tk.Label(nav, text=text, bg=HEADER, fg="#E8D5F0", font=FONT_NAV, cursor="hand2", padx=14)
        lbl.pack(side="left")

        def _make(k=key, c=command):
            def _run(_e=None):
                set_active(k)
                c()

            return _run

        lbl.bind("<Button-1>", _make())
        nav_labels[key] = lbl

    if active_key:
        set_active(active_key)
    return header, set_active


def make_icon(kind, size=18, color="#7A6A8A"):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if kind == "phone":
        d.rounded_rectangle((5, 1, size - 5, size - 1), radius=3, outline=color, width=2)
        d.line((size // 2 - 3, size - 4, size // 2 + 3, size - 4), fill=color, width=2)
    elif kind == "key":
        d.ellipse((2, 2, 12, 12), outline=color, width=2)
        d.rectangle((10, 6, size - 2, 9), fill=color)
        d.rectangle((size - 5, 9, size - 2, 13), fill=color)
    elif kind == "user":
        d.ellipse((5, 2, size - 5, 11), outline=color, width=2)
        d.arc((2, 10, size - 2, size + 6), 200, 340, fill=color, width=2)
    elif kind == "mail":
        d.rectangle((1, 4, size - 2, size - 3), outline=color, width=2)
        d.line((1, 4, size // 2, size // 2 + 1), fill=color, width=2)
        d.line((size - 2, 4, size // 2, size // 2 + 1), fill=color, width=2)
    return ImageTk.PhotoImage(img)
