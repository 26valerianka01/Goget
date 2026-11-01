# geocode_utils.py - геокодирование без платного OpenCage-ключа
import json
import math
import re
import time
import urllib.parse
import urllib.request

_CACHE = {}
_LAST_REQUEST = 0.0


def parse_lat_lng(text):
    """Если строка уже вида '56.83,60.61' - вернуть (lat, lng)."""
    if not text:
        return None
    m = re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*", str(text))
    if not m:
        return None
    a, b = float(m.group(1)), float(m.group(2))
    # lat обычно -90..90; для Екатеринбурга lat≈56, lng≈60
    if abs(a) <= 90 and abs(b) <= 180:
        return a, b
    return None


def geocode_address(address):
    """Вернуть (lat, lng) или None. Сначала парсит координаты, иначе Nominatim."""
    global _LAST_REQUEST
    if address in _CACHE:
        return _CACHE[address]

    parsed = parse_lat_lng(address)
    if parsed:
        _CACHE[address] = parsed
        return parsed

    query = urllib.parse.quote(f"{address}, Екатеринбург")
    url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
    # Nominatim: не чаще 1 запроса в секунду
    elapsed = time.time() - _LAST_REQUEST
    if elapsed < 1.1:
        time.sleep(1.1 - elapsed)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GoGetDeliveryApp/1.0 (goget)"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        _LAST_REQUEST = time.time()
        if data:
            result = (float(data[0]["lat"]), float(data[0]["lon"]))
            _CACHE[address] = result
            return result
    except Exception as e:
        print(f"Ошибка геокодирования '{address}': {e}")
    _CACHE[address] = None
    return None


def haversine_km(coord1, coord2):
    """Расстояние между двумя (lat, lng) в км."""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def distance_between_points(a, b):
    """a/b - адрес или 'lat,lng'. Вернуть км (большое число при ошибке)."""
    c1 = geocode_address(a) if isinstance(a, str) else a
    c2 = geocode_address(b) if isinstance(b, str) else b
    if not c1 or not c2:
        return 1e9
    return haversine_km(c1, c2)
