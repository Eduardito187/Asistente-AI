from app.application.services.analizador_valor_incremental import (
    AnalizadorValorIncremental,
)
from tests._fakes import FakePrecio, FakeProducto


def _p(nombre, cpu, ram, ssd, precio, gpu=None):
    return FakeProducto(
        sku="x", nombre=nombre, procesador=cpu,
        ram_gb=ram, capacidad_gb=ssd, gpu=gpu,
        precio=FakePrecio(precio),
    )


def test_subir_de_8gb_no_gpu_a_16gb_gpu_vale_la_pena():
    barato = _p("Vivobook i5", "Core i5-1334U", 8, 256, 5500)
    caro = _p("Acer Nitro V", "Core i5-13420H", 16, 512, 8799, gpu="GeForce RTX 5050")
    res = AnalizadorValorIncremental.comparar(barato, caro)
    assert res.vale_la_pena is True
    assert res.cambio_gpu is True
    assert res.delta_ram >= 8


def test_mismo_specs_no_vale_la_pena():
    a = _p("Asus i5", "Core i5-1334U", 16, 512, 7000)
    b = _p("HP i5", "Core i5-1334U", 16, 512, 9000)
    res = AnalizadorValorIncremental.comparar(a, b)
    assert res.vale_la_pena is False


def test_solo_cpu_mejora_y_precio_relativo_bajo():
    barato = _p("Vivobook i3", "Core i3-1215U", 16, 512, 7000)
    caro = _p("Asus i7 ultrabook", "Core i7-1355U", 16, 512, 8000)
    res = AnalizadorValorIncremental.comparar(barato, caro)
    assert res.cambio_cpu_tier is True
    assert res.vale_la_pena is True
