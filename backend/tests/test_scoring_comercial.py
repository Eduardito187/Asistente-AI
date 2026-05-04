from app.application.services.scoring_comercial import ScoringComercial
from tests._fakes import FakePerfil, FakePrecio, FakeProducto


def test_producto_que_cumple_todo_alto_score():
    perfil = FakePerfil(
        ram_gb_min=16, ssd_gb_min=512, gpu_dedicada=True,
        presupuesto_ideal=11000, presupuesto_max=11000,
        uso_declarado="ingenieria",
    )
    p = FakeProducto(
        sku="X1", nombre="HP Victus i5 RTX 5050",
        procesador="Core i5-13420H", ram_gb=16, capacidad_gb=512,
        gpu="GeForce RTX 5050", precio=FakePrecio(8799),
    )
    out = ScoringComercial.calcular(p, perfil)
    assert out.score >= 80
    assert "GPU dedicada confirmada" in out.cumple


def test_producto_sin_gpu_pierde_puntaje():
    perfil = FakePerfil(ram_gb_min=16, ssd_gb_min=512, gpu_dedicada=True, uso_declarado="ingenieria")
    p = FakeProducto(
        sku="X2", nombre="Asus Vivobook i5",
        procesador="Core i5-1334U", ram_gb=16, capacidad_gb=512,
        precio=FakePrecio(7000),
    )
    out = ScoringComercial.calcular(p, perfil)
    assert "GPU dedicada" in out.falta
    assert out.score < 60


def test_chromebook_para_ingenieria_descalificado():
    perfil = FakePerfil(uso_declarado="ingenieria")
    p = FakeProducto(
        sku="X3", nombre="Lenovo Chromebook 4GB/32GB eMMC",
        ram_gb=4, capacidad_gb=32, precio=FakePrecio(2500),
    )
    out = ScoringComercial.calcular(p, perfil)
    assert any("Chromebook" in a or "ChromeOS" in a for a in out.advertencias)
    assert out.score <= 20


def test_celeron_para_ingenieria_advertencia():
    perfil = FakePerfil(uso_declarado="ingenieria")
    p = FakeProducto(
        sku="X4", nombre="Asus Celeron N4500",
        procesador="Celeron N4500", ram_gb=4, capacidad_gb=64,
        precio=FakePrecio(3500),
    )
    out = ScoringComercial.calcular(p, perfil)
    assert any("entrada" in a.lower() for a in out.advertencias)
