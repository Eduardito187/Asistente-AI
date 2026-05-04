from app.application.services.asesor_accesorios_contextual import (
    AsesorAccesoriosContextual,
)
from tests._fakes import FakePerfil, FakePrecio, FakeProducto


def test_laptop_para_ingenieria_sugiere_cooler():
    perfil = FakePerfil(uso_declarado="ingenieria")
    p = FakeProducto(sku="X", nombre="HP Victus", categoria="Laptops", precio=FakePrecio(8000))
    accs = AsesorAccesoriosContextual.sugerir(p, perfil)
    keywords = " ".join(a.keyword_busqueda for a in accs).lower()
    assert "cooler" in keywords or "refrigeradora" in keywords


def test_laptop_estudiante_sugiere_audifonos():
    perfil = FakePerfil(uso_declarado="estudio")
    p = FakeProducto(sku="X", nombre="Vivobook i5", categoria="Laptops", precio=FakePrecio(6000))
    accs = AsesorAccesoriosContextual.sugerir(p, perfil)
    keywords = " ".join(a.keyword_busqueda for a in accs).lower()
    assert "audifonos" in keywords or "mouse" in keywords


def test_tv_sugiere_soporte_y_hdmi():
    perfil = FakePerfil()
    p = FakeProducto(sku="X", nombre="LG OLED 55", categoria="TV", precio=FakePrecio(8000))
    accs = AsesorAccesoriosContextual.sugerir(p, perfil)
    keywords = " ".join(a.keyword_busqueda for a in accs).lower()
    assert "soporte" in keywords or "hdmi" in keywords


def test_celular_sugiere_funda_vidrio():
    perfil = FakePerfil()
    p = FakeProducto(sku="X", nombre="Galaxy A55", categoria="Celulares", precio=FakePrecio(3500))
    accs = AsesorAccesoriosContextual.sugerir(p, perfil)
    keywords = " ".join(a.keyword_busqueda for a in accs).lower()
    assert "funda" in keywords or "case" in keywords or "vidrio" in keywords


def test_max_3():
    perfil = FakePerfil(uso_declarado="ingenieria")
    p = FakeProducto(sku="X", nombre="Laptop", categoria="Laptops", precio=FakePrecio(8000))
    accs = AsesorAccesoriosContextual.sugerir(p, perfil)
    assert len(accs) <= 3
