from app.application.services.analizador_riesgo_compra import (
    AnalizadorRiesgoCompra,
    NivelRiesgo,
)
from tests._fakes import FakePerfil, FakePrecio, FakeProducto


def test_chromebook_para_ingenieria_riesgo_alto():
    perfil = FakePerfil(uso_declarado="ingenieria", gpu_dedicada=True, ram_gb_min=16)
    p = FakeProducto(sku="X", nombre="Lenovo Chromebook", ram_gb=4, capacidad_gb=32, precio=FakePrecio(2500))
    e = AnalizadorRiesgoCompra.evaluar(p, perfil)
    assert e.nivel == NivelRiesgo.ALTO
    assert e.badge == "🔴"


def test_laptop_completa_para_oficina_riesgo_bajo():
    perfil = FakePerfil(uso_declarado="oficina", presupuesto_max=8000)
    p = FakeProducto(
        sku="X", nombre="Asus Vivobook i5", procesador="Core i5-1334U",
        ram_gb=16, capacidad_gb=512, precio=FakePrecio(7000),
    )
    e = AnalizadorRiesgoCompra.evaluar(p, perfil)
    assert e.nivel == NivelRiesgo.BAJO
    assert e.badge == "🟢"


def test_falta_gpu_pero_uso_oficina_riesgo_bajo_o_medio():
    perfil = FakePerfil(uso_declarado="oficina", gpu_dedicada=False)
    p = FakeProducto(
        sku="X", nombre="Vivobook i5", procesador="Core i5-1334U",
        ram_gb=16, capacidad_gb=512, precio=FakePrecio(7000),
    )
    e = AnalizadorRiesgoCompra.evaluar(p, perfil)
    assert e.nivel in (NivelRiesgo.BAJO, NivelRiesgo.MEDIO)
