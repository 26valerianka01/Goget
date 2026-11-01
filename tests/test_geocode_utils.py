import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.geocode import parse_lat_lng, haversine_km, distance_between_points


def test_parse_lat_lng():
    assert parse_lat_lng("56.838011,60.597465") == (56.838011, 60.597465)
    assert parse_lat_lng(" 56.8 , 60.6 ") == (56.8, 60.6)
    assert parse_lat_lng("ул. Малышева, 71") is None
    assert parse_lat_lng("") is None


def test_haversine_same_point():
    p = (56.838011, 60.597465)
    assert haversine_km(p, p) == 0


def test_haversine_ekb_distance_reasonable():
    a = (56.838011, 60.597465)
    b = (56.845000, 60.610000)
    d = haversine_km(a, b)
    assert 0.5 < d < 5.0


def test_distance_between_coordinate_strings():
    d = distance_between_points("56.838011,60.597465", "56.838011,60.597465")
    assert d == 0
