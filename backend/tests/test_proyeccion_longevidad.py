from app.application.services.proyeccion_longevidad import ProyeccionLongevidad
from tests._fakes import FakePrecio, FakeProducto


def test_laptop_celeron_dura_2_anios():
    p = FakeProducto(
        sku="X", nombre="Vivobook Celeron",
        categoria="Laptops", procesador="Celeron N4500", ram_gb=4,
        precio=FakePrecio(3500),
    )
    pr = ProyeccionLongevidad.proyectar(p, "estudio")
    assert pr.anios <= 2


def test_laptop_i5_16_512_dura_4_5_anios():
    p = FakeProducto(
        sku="X", nombre="Asus Vivobook i5",
        categoria="Laptops", procesador="Core i5-1334U", ram_gb=16, capacidad_gb=512,
        precio=FakePrecio(8000),
    )
    pr = ProyeccionLongevidad.proyectar(p, "estudio")
    assert pr.anios >= 4


def test_tv_oled_dura_7_anios():
    p = FakeProducto(sku="X", nombre="LG OLED 55", categoria="TV", precio=FakePrecio(8000))
    p.tipo_panel = "OLED"
    pr = ProyeccionLongevidad.proyectar(p, None)
    assert pr.anios >= 6


def test_smartphone_flagship_dura_4():
    p = FakeProducto(sku="X", nombre="Galaxy S26 Ultra", categoria="Celulares", precio=FakePrecio(12000))
    pr = ProyeccionLongevidad.proyectar(p, None)
    assert pr.anios == 4
