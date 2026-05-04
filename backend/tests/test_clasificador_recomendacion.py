from app.application.services.clasificador_recomendacion import (
    ClasificadorRecomendacion,
    NivelRecomendacion,
)
from tests._fakes import FakePerfil, FakePrecio, FakeProducto


def test_producto_que_cumple_todo_es_ideal():
    perfil = FakePerfil(ram_gb_min=16, ssd_gb_min=512, gpu_dedicada=True, presupuesto_max=11000, uso_declarado="ingenieria")
    p = FakeProducto(
        sku="X1", nombre="HP Victus i5",
        procesador="Core i5-13420H", ram_gb=16, capacidad_gb=512,
        gpu="GeForce RTX 5050", precio=FakePrecio(8799),
    )
    c = ClasificadorRecomendacion.clasificar(p, perfil)
    assert c.nivel == NivelRecomendacion.IDEAL
    assert c.puede_ser_principal is True


def test_chromebook_para_ingenieria_no_recomendable():
    perfil = FakePerfil(uso_declarado="ingenieria", ram_gb_min=16, gpu_dedicada=True)
    p = FakeProducto(
        sku="X2", nombre="Lenovo Chromebook 4GB",
        ram_gb=4, capacidad_gb=32, precio=FakePrecio(2500),
    )
    c = ClasificadorRecomendacion.clasificar(p, perfil)
    assert c.nivel == NivelRecomendacion.NO_RECOMENDABLE
    assert c.puede_ser_principal is False


def test_sin_gpu_pero_uso_oficina_no_falla_obligatorios():
    perfil = FakePerfil(ram_gb_min=8, uso_declarado="oficina", presupuesto_ideal=6000, presupuesto_max=6000)
    p = FakeProducto(
        sku="X3", nombre="Asus Vivobook i5",
        procesador="Core i5-1334U", ram_gb=8, capacidad_gb=256,
        precio=FakePrecio(5500),
    )
    c = ClasificadorRecomendacion.clasificar(p, perfil)
    # No esta entre los descartados (NO_RECOMENDABLE) — eso es lo critico.
    assert c.nivel != NivelRecomendacion.NO_RECOMENDABLE
