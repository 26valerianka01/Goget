# map_display.py
from tkinter import ttk
import folium
import webbrowser
from app.db.catalog import get_connection
from mysql.connector import Error
from app.services.geocode import geocode_address
import threading
import random
from tkinter import messagebox


def get_random_color():
    return random.choice(
        [
            "blue",
            "pink",
            "orange",
            "darkred",
            "purple",
            "green",
            "darkpurple",
            "cadetblue",
            "darkgreen",
            "darkblue",
            "red",
            "lightred",
        ]
    )


def display_map(map_frame):
    for widget in map_frame.winfo_children():
        if isinstance(widget, ttk.Label) and widget.cget("text") == "Карта строится...":
            widget.destroy()
    status = ttk.Label(map_frame, text="Карта строится...", font=("Arial", 12))
    status.pack(pady=10)
    map_frame.update_idletasks()

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id_маршрут FROM Маршрут")
        routes = cursor.fetchall()

        m = folium.Map(location=[56.838011, 60.597465], zoom_start=12)

        if not routes:
            folium.Marker([56.838011, 60.597465], popup="Нет маршрутов").add_to(m)
        else:
            for route in routes:
                route_id = route[0]
                color = get_random_color()
                cursor.execute(
                    "SELECT координаты_ТочкиМаршрута, тип_ТочкиМаршрута, id_заказы "
                    "FROM ТочкиМаршрута WHERE id_маршрут = %s",
                    (route_id,),
                )
                points = cursor.fetchall()

                coordinates = []
                for point in points:
                    coord, point_type, order_id = point
                    location = geocode_address(coord)
                    if not location:
                        continue
                    lat, lng = location
                    coordinates.append((lat, lng))

                    delivery_address = ""
                    items = []
                    if order_id:
                        cursor.execute(
                            "SELECT адрес_доставка FROM Заказы WHERE id_заказы = %s",
                            (order_id,),
                        )
                        row = cursor.fetchone()
                        delivery_address = row[0] if row else ""
                        cursor.execute(
                            "SELECT t.название_товары, tvz.количество, m.название_магазин, m.адрес_магазин "
                            "FROM ТоварыВЗаказе tvz "
                            "JOIN Товары t ON tvz.id_товара = t.id_товары "
                            "JOIN Магазин m ON t.id_магазин = m.id_магазин "
                            "WHERE tvz.id_заказа = %s",
                            (order_id,),
                        )
                        items = cursor.fetchall()

                    if point_type == "забрать":
                        items_text = "\n".join(
                            [f"Забрать из {item[2]} ({item[3]}), Товар: {item[0]} x {item[1]}" for item in items]
                        )
                        popup_text = f"{coord}\n{items_text}"
                    else:
                        items_text = "\n".join([f"Товар: {item[0]} x {item[1]}" for item in items])
                        popup_text = f"Адрес доставки: {delivery_address}\nДоставить: {items_text}"

                    folium.Marker([lat, lng], popup=popup_text, icon=folium.Icon(color=color)).add_to(m)

                if len(coordinates) > 1:
                    folium.PolyLine(coordinates, color=color, weight=2.5, opacity=1).add_to(m)

        map_file = "map.html"
        m.save(map_file)
        threading.Thread(target=lambda: webbrowser.open(map_file), daemon=True).start()
        status.config(text="Карта открыта в браузере")
    except Error as e:
        messagebox.showerror("Ошибка", f"Ошибка при получении маршрутов: {e}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка карты: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
