"""Надёжный вертикальный скролл Canvas + колесо мыши (Windows)."""
from __future__ import annotations

import tkinter as tk


def make_scrollable(parent, bg="#F4F6F8", padx=(0, 0), pady=(0, 0)):
    """
    Возвращает (outer, canvas, inner).
    Кладите виджеты в inner - колесо работает над любым дочерним элементом.
    """
    outer = tk.Frame(parent, bg=bg)
    canvas = tk.Canvas(outer, bg=bg, highlightthickness=0, bd=0)
    scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=bg)

    window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    def _sync_scrollregion(_event=None):
        canvas.update_idletasks()
        bbox = canvas.bbox("all")
        if bbox:
            canvas.configure(scrollregion=bbox)

    def _sync_width(event):
        # внутренняя рамка = ширина canvas → grid с weight растягивается без дыры справа
        w = max(event.width, 1)
        canvas.itemconfigure(window_id, width=w)
        try:
            inner.configure(width=w)
        except tk.TclError:
            pass

    def _on_wheel(event):
        try:
            if not canvas.winfo_exists():
                return
            # быстрее и заметнее, чем 1 unit
            steps = int(-1 * (event.delta / 120))
            if steps == 0:
                steps = -1 if event.delta > 0 else 1
            canvas.yview_scroll(steps * 3, "units")
        except tk.TclError:
            pass
        return "break"

    def _bind_tree(widget):
        widget.bind("<MouseWheel>", _on_wheel, add="+")
        for child in widget.winfo_children():
            _bind_tree(child)

    def _rebinding(_event=None):
        _sync_scrollregion()
        _bind_tree(inner)

    inner.bind("<Configure>", _rebinding)
    canvas.bind("<Configure>", _sync_width)
    canvas.bind("<MouseWheel>", _on_wheel)

    # когда курсор в зоне скролла - глобально ловим колесо (но только если canvas жив)
    def _enter(_event=None):
        canvas.bind_all("<MouseWheel>", _on_wheel)

    def _leave(event):
        # не снимаем bind, если ушли на дочерний виджет внутри canvas/inner
        try:
            widget = canvas.winfo_containing(event.x_root, event.y_root)
            if widget is None:
                canvas.unbind_all("<MouseWheel>")
                return
            w = str(widget)
            if not (w.startswith(str(canvas)) or w.startswith(str(inner))):
                canvas.unbind_all("<MouseWheel>")
        except tk.TclError:
            try:
                canvas.unbind_all("<MouseWheel>")
            except tk.TclError:
                pass

    canvas.bind("<Enter>", _enter)
    inner.bind("<Enter>", _enter)
    canvas.bind("<Leave>", _leave)
    inner.bind("<Leave>", _leave)

    def _cleanup(_event=None):
        try:
            canvas.unbind_all("<MouseWheel>")
        except tk.TclError:
            pass

    canvas.bind("<Destroy>", _cleanup)

    if isinstance(padx, tuple):
        outer.pack(fill="both", expand=True, padx=padx, pady=pady)
    else:
        outer.pack(fill="both", expand=True, padx=padx, pady=pady)

    return outer, canvas, inner
