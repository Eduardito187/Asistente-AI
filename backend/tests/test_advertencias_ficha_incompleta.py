from app.application.services.advertencias_ficha_incompleta import (
    AdvertenciasFichaIncompleta,
)
from tests._fakes import FakeProducto


def test_uso_ingenieria_falta_gpu_emite_advertencia():
    p = FakeProducto(sku="X", nombre="Asus i5", ram_gb=16, capacidad_gb=512)
    warns = AdvertenciasFichaIncompleta.advertencias(p, "ingenieria")
    assert any("GPU dedicada" in w for w in warns)


def test_uso_oficina_no_exige_gpu():
    p = FakeProducto(sku="X", nombre="Asus i5", ram_gb=16, capacidad_gb=512)
    warns = AdvertenciasFichaIncompleta.advertencias(p, "oficina")
    assert all("GPU" not in w for w in warns)


def test_sin_uso_no_emite_advertencias():
    p = FakeProducto(sku="X", nombre="Asus i5", ram_gb=16, capacidad_gb=512)
    assert AdvertenciasFichaIncompleta.advertencias(p, None) == []


def test_uso_render_falta_ram_y_gpu():
    p = FakeProducto(sku="X", nombre="Vivobook")
    warns = AdvertenciasFichaIncompleta.advertencias(p, "render")
    assert any("GPU" in w for w in warns)
    assert any("RAM" in w for w in warns)
